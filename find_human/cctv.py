from pathlib import Path
import tkinter as tk
from PIL import Image, ImageTk, UnidentifiedImageError
from zipfile import ZipFile, BadZipFile
import cv2
import numpy as np

zip_path = Path("cctv.zip")
img_dir  = Path("cctv")

def extract_zipfile():
    try:
        if not zip_path.is_file():
            raise FileNotFoundError("CCTV.zip 파일을 찾을 수 없습니다.")

        img_dir.mkdir(exist_ok=True)  # 이미 있으면 그대로 사용
        with ZipFile(zip_path, "r") as zf:
            zf.extractall(img_dir)

        print(f"압축 해제 완료: {img_dir.resolve()}")

    except FileNotFoundError as e:
        print(e)
    except BadZipFile:
        print("압축 파일이 손상됐거나 ZIP 형식이 아닙니다.")
    except Exception as e:
        print(f"Error: {e}")


class ImageLabel(tk.Label):
    _photo: ImageTk.PhotoImage | None = None
    def set_image(self, pil_img: Image.Image) -> None:
        self._photo = ImageTk.PhotoImage(pil_img)
        self.config(image=self._photo)


class MasImageHelper:
    """간단한 이미지 뷰어: ←/→ 키로 이전·다음 이동"""
    def __init__(self, img_dir="cctv", exts=None):
        self.img_dir = Path(img_dir)
        self.exts = exts or {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff"}
        if not self.img_dir.is_dir():
            raise FileNotFoundError("CCTV 폴더를 찾을 수 없습니다.")
        self.images = sorted([p for p in self.img_dir.iterdir() if p.suffix.lower() in self.exts])
        if not self.images:
            raise FileNotFoundError("CCTV 폴더에 이미지 파일이 없습니다.")

        self.idx = 0
        self.root = tk.Tk()
        self.root.title("CCTV Viewer")
        self.root.configure(background="black")
        self.label = ImageLabel(self.root, bg="black")
        self.label.pack(fill="both", expand=True)

        # 키 바인딩
        self.root.bind("<Right>", self.next)
        self.root.bind("<Left>", self.prev)
        self.root.bind("<Return>", self.search_people)  # Enter
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("q", lambda e: self.root.destroy())

        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())


    def _fit_to_screen(self, img: Image.Image) -> Image.Image:
        """화면 크기에 맞게 축소(여백 포함)"""
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        margin_w, margin_h = 100, 160
        max_w, max_h = max(200, sw - margin_w), max(200, sh - margin_h)
        img = img.copy()
        img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS) # thumbnail은 크기를 원본 비율을 유지하면서 resize() 기능을 제공
        return img
    
    def _cv_to_pil(self, img_bgr: np.ndarray) -> Image.Image:
        """OpenCV BGR -> PIL Image (RGB)"""
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)

    def show_path(self, path: Path, title_prefix: str = "") -> None:
        """주어진 경로 이미지를 표시"""
        try:
            pil_img = Image.open(path)
        except UnidentifiedImageError:
            # 손상/미지원 포맷이면 다음으로
            self.next()
            return
        pil_img = self._fit_to_screen(pil_img)
        self.label.set_image(pil_img)
        prefix = (title_prefix + " ") if title_prefix else ""
        self.root.title(f"{prefix}{self.idx+1}/{len(self.images)} - {path.name}")

    def show(self, i: int) -> None:
        """i번째 이미지 표시(인덱스 래핑)"""
        self.idx = i % len(self.images)
        self.show_path(self.images[self.idx])

    # 이벤트 핸들러(인자 event는 무시)
    def next(self, event=None):
        self.show(self.idx + 1)

    def prev(self, event=None):
        self.show(self.idx - 1)

    def _detect_people(self, img_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
        """
        HOG+SVM 보행자 검출.
        속도를 위해 내부적으로 축소해서 탐지 후 원본 좌표로 되돌림.
        반환: [ (x, y, w, h), ... ] (원본 좌표계)
        """
        h, w = img_bgr.shape[:2]

        # 너무 큰 이미지는 축소해서 탐지(속도↑). 기준은 짧은 변 720px.
        target_short = 720
        scale = 1.0
        if min(w, h) > target_short:
            if w < h:
                scale = target_short / w
            else:
                scale = target_short / h
        if scale < 1.0:
            resized = cv2.resize(img_bgr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)
        else:
            resized = img_bgr

        rects, _ = self.hog.detectMultiScale(
            resized,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05
        )

        # 좌표를 원본 크기로 되돌리기
        inv = (1.0 / scale) if scale < 1.0 else 1.0
        boxes: list[tuple[int, int, int, int]] = []
        for (x, y, rw, rh) in rects:
            X = int(x * inv)
            Y = int(y * inv)
            W = int(rw * inv)
            H = int(rh * inv)
            boxes.append((X, Y, W, H))
        return boxes

    def _try_show_with_detections(self, path: Path) -> bool:
        """
        이미지를 로드하여 사람 검출. 하나 이상 발견되면 박스 그려 표시하고 True, 아니면 False.
        """
        img_bgr = cv2.imread(str(path))
        if img_bgr is None:
            return False
        boxes = self._detect_people(img_bgr)
        if not boxes:
            return False

        self.root.title(f"FOUND 👤  {self.idx+1}/{len(self.images)} - {path.name}")
        return True

    # ---------- Enter: 순차 검색 ----------
    def search_people(self, event=None) -> None:
        """
        현재 idx부터 앞으로 순차적으로 탐색.
        사람 발견 시 해당 이미지에서 정지하여 표시.
        한 바퀴 돌아도 없으면 타이틀에 미발견 표시.
        """
        start = self.idx
        n = len(self.images)

        for step in range(n):
            i = (start + step) % n
            self.idx = i
            path = self.images[i]
            # 먼저 화면에 로드(UX), 곧바로 탐지 시도
            self.show_path(path, title_prefix="SEARCHING…")
            self.root.update_idletasks()

            found = self._try_show_with_detections(path)
            if found:
                return  # 여기서 멈춤

        # 한 바퀴 돌았는데도 못 찾음
        self.root.title("NO PERSON FOUND")

    def start(self):
        """뷰어 실행"""
        self.show(0)
        self.root.mainloop()

def main():
    try:
        #extract_zipfile()
        MasImageHelper("cctv").start()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
