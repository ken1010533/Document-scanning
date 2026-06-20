import hashlib

def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            data = f.read(1024 * 1024)
            if not data:
                break
            h.update(data)  
    return h.hexdigest()

a = r"C:\Users\a\Desktop\your_project\設定.json"
b = r"C:\Users\a\Desktop\your_project\設定 - 複製.json"

print(md5(a))
print(md5(b))