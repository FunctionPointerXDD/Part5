

alpha = string.ascii_lowercase

def decode_list(code: str) -> list:
	code_list = []
	for shift in range(len(alpha)):
		decoded = ''
		for ch in code:
			if ch.isalpha():
				decoded += chr((ord(ch) - 'a' - shift) % 26 + 'a')
			else:
				decoded += ch
		print(f'{shift}: {decoded}'}
		code_list.append(decoded)

	retrun code_list

