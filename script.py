import hashlib
import os
import subprocess

GAME_DIR    = "K:/SteamLibrary/steamapps/common/Full Spectrum Warrior"
BACKUP_DLL  = GAME_DIR + "\\FSW.dll.BAK.ORIGINAL"
TARGET_DLL  = GAME_DIR + "\\FSW.dll" 

RVA_BASE = 0x10000000 # relative address base of the .text section of the FSW.dll

def bytes_to_dec(barr):
    r = 0
    blen = len(barr)
    for i in range(blen):
        o = blen-1-i
        r |= ( (barr[i] & 0xff) << o*8)
    return r

def dec_to_bytes(dec):
    return bytearray.fromhex(hex(dec)[2:])

def endi_swap_dec(dec):
    arr = dec_to_bytes(dec)
    r = 0
    blen = len(arr)
    for i in range(blen):
        o = blen-1-i
        r |= ((arr[o]&0xff) << o*8)
    return r

def endi_swap_bytes(arr):
    r = bytearray()
    blen = len(arr)
    for i in range(blen):
        o = blen-1-i
        r.append(arr[o])
    return bytes(r)

def read_file(path, mode="rb"):
    with open(path, mode) as f:
        data = f.read()
    return data

def save_file(path, data, mode="wb"):
    if os.path.exists(path): os.remove(path)
    with open(path, mode) as f:
        f.write(data)
    return

def asm_to_bin(asm_str, add_bits_indicator=True):
    if add_bits_indicator:
        asm_str = "bits 32\n" + asm_str

    with open("./tmp/nasm_assm.asm", "wt") as f:
        f.write(asm_str)
    cmd = ["nasm.exe", "-Wx", "-Werror=all", "-f bin", "./tmp/nasm_assm.asm"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    process.wait()
    if process.returncode != 0:
        print(process.stderr)
        exit(1) 
    return read_file("./tmp/nasm_assm")

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
    save_file("./tmp/nasm_disassm", bin)
    return binfile_to_asm("./tmp/nasm_disassm")

def boba(addr, base = RVA_BASE): # (file) byte offset based on relative address 
    if addr < base: return addr
    return (addr - base)

def do_patch(original_bytes, offset, replacement_bytes):
    return original_bytes[:offset] + replacement_bytes + original_bytes[offset + len(replacement_bytes):]

# /////////////////////////PATCH/////////////////////////////

dll = read_file(BACKUP_DLL)
dllbak = dll

# call [ecx] (QueryInterface()) -> call 0x105F836A \ nop
bin = asm_to_bin("call 0x105F836A-0x102E74AF\n nop\n", True) # b"\xE8\xB6\x0E\x31\x00\x90"
dll = do_patch(dll, boba(0x102E74AF), bin)

patch = read_file('./patch.asm', "rt")
patch = asm_to_bin(patch, add_bits_indicator=False)
dll = do_patch(dll, boba(0x105F836A), patch)

# //////////////////////////CHECKS///////////////////////////

original_dll_hash = hashlib.md5(dllbak).hexdigest()
patched_dll_hash = hashlib.md5(dll).hexdigest()
print("\nhash: {} -> {}".format(original_dll_hash, patched_dll_hash))

assert(len(dll) == len(dll))

save_file(TARGET_DLL, dll)

assert(len(read_file(BACKUP_DLL)) == len(read_file(TARGET_DLL)))

print("\nDONE!\n")