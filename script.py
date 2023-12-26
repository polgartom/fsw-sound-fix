# import shutil
import hashlib
import os
import subprocess
import struct

GAME_DIR   = r"K:\SteamLibrary\steamapps\common\Full Spectrum Warrior"
PATCH_PATH = r"C:\Users\polga\Desktop\FSW Reverse\result.bin"
BACKUP_DLL = GAME_DIR + "\\FSW.dll.BAK.ORIGINAL"
TARGET_DLL = GAME_DIR + "\\FSW.dll" 

RVA_BASE = 0x10000000 # relative address base of the .text section of the FSW.dll

# little endian
def unpack_le_4b(bin):
    return struct.unpack('>I', bin)[0]

# big endian
def unpack_be_4b(bin):
    return struct.unpack('<I', bin)[0]

def endi_swap(bin):
    r = 0
    blen = len(bin)
    for i in range(blen):
        o = blen-1-i
        r |= ((bin[o]&0xff) << o*8)
    return r

def readfb(path):
    with open(path, "rb") as f:
        data = f.read()
    return data
    
def savefb(path, data):
    if os.path.exists(path): os.remove(path)
    with open(path, "wb") as f:
        f.write(data)
    return

def asm_to_bin(asm_str):
    asm_str = "bits 32\n" + asm_str
    with open("./tmp/nasm_assm.asm", "wt") as f:
        f.write(asm_str)
    cmd = ["nasm.exe", "-Wx", "-Werror=all", "-f bin", "./tmp/nasm_assm.asm"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    process.wait()
    if process.returncode != 0:
        print(process.stderr)
        exit(1) 
    return readfb("./tmp/nasm_assm")

def binfile_to_asm(bin_filepath):
    cmd = ["ndisasm.exe", "-b32", bin_filepath]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    process.wait()
    if process.returncode != 0:
        print(process.stderr)
        exit(1) 
    asm_str = ""
    for l in process.stdout:
        l = l.decode()
        s = l.split(' ')[3:]        # skip offset and hex representation
        while s[0] == '': s = s[1:] # trim whitespaces
        asm_str += ' '.join(s)
    return asm_str

def bin_to_asm(bin):
    savefb("./tmp/nasm_disassm", bin)
    return binfile_to_asm("./tmp/nasm_disassm")

# (file) byte offset based on relative address 
def boba(addr, base = RVA_BASE):
    assert(addr >= base)
    return (addr - base)

def do_patch(original_bytes, replacement_bytes, offset):
    return original_bytes[:offset] + replacement_bytes + original_bytes[offset + len(replacement_bytes):]
    
dll = readfb(BACKUP_DLL)
patch = readfb(PATCH_PATH)

result = dll
# result = do_patch(result, b"\xe9\x45\xbe\x30\x00", boba(0x102E74AF)) # ret 0x4 -> jmp (0x30be4a(base)+0x102E74AF(offset))=0x105F836A

# call [ecx] (QueryInterface()) -> call 0x105F836A \ nop
bin = asm_to_bin("call 0x105F836A-0x102E74AF\n nop\n") # b"\xE8\xB6\x0E\x31\x00\x90"
print(bin_to_asm(bin))
result = do_patch(result, bin, boba(0x102E74AF))

result = do_patch(result, patch, boba(0x105F836A))

assert(len(dll) == len(result))

savefb(TARGET_DLL, result)

assert(len(readfb(BACKUP_DLL)) == len(readfb(TARGET_DLL)))

print("\nDONE!\n")