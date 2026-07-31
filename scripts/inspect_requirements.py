from pathlib import Path
p = Path('requirements.txt')
data = p.read_bytes()
print('raw bytes:', data[:200])
for enc in ['utf-8','utf-8-sig','utf-16','utf-16-le','utf-16-be','latin-1']:
    try:
        text = data.decode(enc)
        print('ENC', enc, '->', repr(text[:500]))
    except Exception as e:
        print('ENC', enc, 'ERR', e)
