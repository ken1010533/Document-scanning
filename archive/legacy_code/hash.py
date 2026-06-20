import hashlib
from concurrent.futures import ThreadPoolExecutor

def 計算檔案hash(檔案路徑):
    h = hashlib.md5()
    with open(檔案路徑, 'rb') as f:
        for 區塊 in iter(lambda: f.read(8192), b''):
            h.update(區塊)
    return h.hexdigest()


def 快速hash(檔案路徑):
    import hashlib
    h = hashlib.md5()
    with open(檔案路徑, 'rb') as f:
        h.update(f.read(4096))
    return h.hexdigest()


def 平行hash(檔案列表):
    with ThreadPoolExecutor(max_workers=8) as executor:
        return list(executor.map(快速hash, 檔案列表))