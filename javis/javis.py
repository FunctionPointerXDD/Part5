#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import glob
import csv
import json
import sys
import queue
from datetime import datetime
import sounddevice as sd
import soundfile as sf
from typing import Any
from numpy import ndarray

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDS_DIR = os.path.join(BASE_DIR, "records")
os.makedirs(RECORDS_DIR, exist_ok=True)


def default_samplerate(device: int | None) -> int:
    try:
        info = sd.query_devices(device, 'input')
        sr = int(info.get('default_samplerate', 44100)) # 샘플링 레이트: 44.1kHz -> 아날로그 신호를 디지털 신호로 변환할 때 1초에 몇 번의 샘플을 추출하는지를 나타내는 값
        return sr if sr > 0 else 44100
    except Exception:
        return 44100

def record_once():
    device = sd.default.device[0]
    if device is None:
        print("[오류] 입력 가능한 마이크 장치를 찾지 못했습니다.")
        return

    sr = default_samplerate(device)
    channels = 1  # 단일 채널(모노 사운드), 2로 주면 스테레오 타입으로 사운드 저장(용량 더 커짐)
    filename = datetime.now().strftime("%Y%m%d-%H%M%S") + ".wav"
    filepath = os.path.join(RECORDS_DIR, filename)

    print("\n[안내] 녹음 파일 경로:", filepath)

    try:
        devinfo: Any | dict[str, Any] = sd.query_devices(device, 'input')
        print(f"[장치] {devinfo.get('name')} / 채널={devinfo.get('max_input_channels')} / 기본 SR={int(devinfo.get('default_samplerate', sr))}")
    except Exception:
        pass

    # 파이썬에서 제공하는 큐로 사용자 입력과 녹음 기능을 안전하게 분리할 수 있다. 큐 내부적으로 write할 때 락 기능 제공!
    q = queue.Queue()

    #duration 없이 사용자가 입력하기 전까지 계속 녹음하기 위한 용도
    def callback(indata: ndarray, frames, time, status):
        if status: #indata buffer의 overflow underflow 상태 점검 용도
            print(f"[경고] {status}", file=sys.stderr)
        q.put(indata.copy())

    print("[녹음 시작] 종료하려면 Enter 또는 Ctrl+C 를 누르세요.")
    try:
        with (
            sf.SoundFile(filepath, mode="x", samplerate=sr, channels=channels, subtype="PCM_24") as f, # PCM_24가 PCM_16보다 저장하는 음성데이터 폭이 더 넓다.
            sd.InputStream(samplerate=sr, device=device, channels=channels, callback=callback) # device buffer에 녹음하면 주기적으로 callback 되면서 큐에 저장
        ):
            try: # 사용자 입력 받아서 녹음 종료하는 용도로 스레드 생성해서 따로 돌림.. '\n' 입력하면 정상 종료됨.
                import threading
                stop = threading.Event()

                def wait_enter():
                    try:
                        input()
                    except Exception:
                        pass
                    stop.set()

                waiter = threading.Thread(target=wait_enter, daemon=True)
                waiter.start()

                while not stop.is_set():
                    try:
                        data = q.get(timeout=0.1) #계속 큐에서 대기 안하고 100ms 마다 stop 이벤트 확인
                        f.write(data) # 파일에 녹음하기
                    except queue.Empty: # 비어있는 경우는 거의 없긴함.. 그래도 예외처리
                        pass
            except KeyboardInterrupt:
                print("\n[중단] Ctrl+C 감지.")
    except FileExistsError:
        print("[오류] 동일한 이름의 파일이 이미 존재합니다. 잠시 후 다시 시도하세요.")
        return
    except Exception as e:
        print("[오류] 녹음 중 문제가 발생했습니다:", e)
        return

    print("[완료] 저장됨 →", filepath)


## <---------- 녹음 파일 읽는 메서드 ----------> ##

def list_record_wavs() -> list[str]:
    pattern = os.path.join(RECORDS_DIR, "*.wav")
    files = glob.glob(pattern)
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files


def stt_transcribe_wav_to_csv(wav_path: str, model_path: str | None = None) -> str | None:
    from vosk import Model, KaldiRecognizer
    # 결과 CSV 경로
    csv_path = os.path.splitext(wav_path)[0] + ".CSV"

    # 모델 로드
    print(f"[STT] 모델 로드: {model_path}")
    model = Model(model_path)

    # 스트리밍으로 읽으며 처리 (메모리 절약)
    with sf.SoundFile(wav_path, "r") as f:
        sr = f.samplerate

        # KaldiRecognizer에 samplerate 전달
        rec = KaldiRecognizer(model, sr)
        rec.SetWords(True)

        rows: list[tuple[str, str]] = []
        # 0.1초(= sr/10 프레임) 단위로 읽기
        block = max(1, sr // 10)

        while True:
            # int16로 읽으면 바로 PCM 바이트로 넘기기 쉬움
            data = f.read(frames=block, dtype="int16")
            if len(data) == 0:
                break

            # Vosk에 공급 (바이트)
            ok = rec.AcceptWaveform(data.tobytes())
            if ok:
                j = json.loads(rec.Result())
                # j 예: {"result":[{"word":"...", "start":0.12, "end":0.45}, ...], "text":"..."}
                if "result" in j:
                    words = j["result"]
                    text = j.get("text", "").strip()
                    if words and text:
                        start = words[0]["start"]
                        end = words[-1]["end"]
                        rows.append((f"{start:.2f}-{end:.2f}", text))

        # 마지막 누적 결과
        j = json.loads(rec.FinalResult())
        if "result" in j:
            words = j["result"]
            text = j.get("text", "").strip()
            if words and text:
                start = words[0]["start"]
                end = words[-1]["end"]
                rows.append((f"{start:.2f}-{end:.2f}", text))

    # CSV 저장 (UTF-8)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as out:
        w = csv.writer(out)
        w.writerow(["음성 파일내에서의 시간", "인식된 텍스트"])
        for t, txt in rows:
            w.writerow([t, txt])

    # 콘솔에 간단 프리뷰(인식 품질 확인용)
    print(f"[STT] 저장 완료: {csv_path}")
    for preview in rows[:3]:
        print(f"  [미리보기] {preview[0]}  {preview[1]}")
    if not rows:
        print("  [주의] 인식된 문장이 없습니다. (소음/볼륨/모델 언어 확인 필요)")

    return csv_path


def stt_process_records(model_path: str | None = None):
    files = list_record_wavs()
    if not files:
        print("[STT] 처리할 WAV 파일이 없습니다. records 폴더를 확인하세요.")
        return
    print(f"[STT] 대상 파일 수: {len(files)}")
    for i, wav in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {os.path.basename(wav)}")
        stt_transcribe_wav_to_csv(wav, model_path=model_path)


def main():
    ans = input("녹음을 시작할까요? (y/N): ").strip().lower()
    if ans not in ("y", "yes"):
        print("종료합니다.")
        return
    record_once()
    stt_process_records('./vosk/vosk-model-small-en-us-0.15')


if __name__ == "__main__":
    main()