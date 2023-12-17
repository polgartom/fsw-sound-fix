# import shutil
import hashlib
import os

GAME_DIR   = r"K:\SteamLibrary\steamapps\common\Full Spectrum Warrior"
PATCH_PATH = r"C:\Users\polga\Desktop\FSW Reverse\result.bin"
BACKUP_DLL = GAME_DIR + "\\FSW.dll.BAK.ORIGINAL"
TARGET_DLL = GAME_DIR + "\\FSW.dll" 

RVA_BASE = 0x10000000 # relative address base of the .text section of the FSW.dll

# file byte offset from relative address 
def boba(addr, base = RVA_BASE):
    assert(addr >= base)
    return (addr - base)

def do_patch(original_bytes, replacement_bytes, offset):
    return original_bytes[:offset] + replacement_bytes + original_bytes[offset + len(replacement_bytes):]
    
def readfb(path):
    f = open(path, "rb")
    data = f.read()
    f.close()
    return data
    
def savefb(path, data):
    if os.path.exists(path): os.remove(path)
    f = open(path, "wb")
    f.write(data)
    f.close()
    return

dll = readfb(BACKUP_DLL)
patch = readfb(PATCH_PATH)

result = dll
# result = do_patch(result, b"\xe9\x45\xbe\x30\x00", boba(0x102E74AF)) # ret 0x4 -> jmp 0x105F836A
result = do_patch(result, b"\xE8\xB6\x0E\x31\x00\x90", boba(0x102E74AF)) # call [ecx] (QueryInterface()) -> call 0x105F836A \ nop
result = do_patch(result, patch, boba(0x105F836A))

assert(len(dll) == len(result))

savefb(TARGET_DLL, result)

print(hashlib.md5(dll).hexdigest())
print(hashlib.md5(result).hexdigest())

assert(len(readfb(BACKUP_DLL)) == len(readfb(TARGET_DLL)))

print("\n")
print("DONE")
print("\n")