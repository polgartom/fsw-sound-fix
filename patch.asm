bits 32

%macro CODE_START 0

	pushfd 			; save the flags
	push ebp		; save
	mov ebp, esp	;	the stack ptr current state

	; save the registers
	push eax
	push ebx
	push ecx
	push edx
	push ebp
	push esp
	push esi
	push edi
	
%endmacro

%macro CODE_END 0

	; restore the registers
	pop edi
	pop esi
	pop esp
	pop ebp
	pop edx
	pop ecx
	pop ebx
	pop eax

	; restore stack ptr
	mov esp, ebp
	pop ebp
	popfd	; restore the flags
	
%endmacro

%define WORD  0x2
%define DWORD 0x4

; The starting memory is a free accessible memory space somewhere in the .data segment, 
; we use this some kinda storage, because working with the heap in this case just a
; pain in the ass, therefore we use a CURSOR macro with others macros to increment and keep
; track of the value of it.
%define START_MEM  0x10A29429
%define CURSOR 	   START_MEM ; free, accesible pointer in FSW.dll

%macro __IncrementCursor 1
	%assign CURSOR CURSOR+%1
%endmacro

%define IncrementCursor(__size) __IncrementCursor __size

%macro var 2-3	; var_name, var_size_in_bytes; init_value (optional)

	%assign %1 CURSOR
	IncrementCursor(%2)

	%ifnempty %3
		mov dword ds:[%1], %3
	%endif

%endmacro

%define ASSERT() mov dword ds:[0x0], 0xFFFFF

; ////////////////////////////////////////////

; Simulating PrimaryBuffer->QueryInterace(REFID, (LPVOID*)&LPDIRECTSOUNDBUFFER8)

; 0x105F836A our start address

; where we're coming from
%define ComingFromAddress 0x102E74AF
%define ArgumentCount 	  0x3 ; +0x1, because of the *PrimaryBuffer

%define DirectSound 		  0x10747EA0
%define PrimaryBuffer		  0x10747EA4
%define GlobalSecondaryBuffer 0x10747EAC

CODE_START

mov ecx, dword ds:[DirectSound]
and ecx, dword ds:[PrimaryBuffer]
jz _out ; at this point the directsound and the primarybuffer is not initialized yet

and ecx, dword ds:[GlobalSecondaryBuffer]
jnz _out ; initialized once already!

; Make some space for the comparison as you can see above,
; basically just skipping (reserve) the first 4 byte
IncrementCursor(DWORD)

; Prepare to call the CreateSoundBuffer
var HRESULT, DWORD, 0

var wFormatTag, 		WORD,  0x1 ; WAVE_FORMAT_PCM
var nChannels, 			WORD,  0x2
var nSamplesPerSec, 	DWORD, 48000
var nAvgBytesPerSec, 	DWORD, 192000
var nBlockAlign, 		WORD,  4
var wBitsPerSample, 	WORD,  16
var cbSize, 			WORD,  0
%define WaveFormat wFormatTag

var dwSize, 		DWORD, 0x24
var dwFlags, 		DWORD, 0x00010000 ; DSBCAPS_GETCURRENTPOSITION2
var dwBufferBytes,  DWORD, 192000
var dwReserved, 	DWORD, 0
var lpwfxFormat, 	DWORD, WaveFormat
var _GUID,			(0x24-(CURSOR-dwSize)), 0x0
%define BufferDescription dwSize

; DirectSound->CreateSoundBuffer(...)
_create_sound_buffer:
push 0
push GlobalSecondaryBuffer
push BufferDescription
mov ecx, dword ds:[DirectSound]
push ecx
mov ecx, [ecx]
call [ecx+0x0c]
mov dword ds:[HRESULT], eax
cmp eax, 0x0
je _play
int3
ASSERT()

; GlobalSecondaryBuffer->Play()
_play:
push 0x1 ; DSBPLAY_LOOPING
push 0x0
push 0x0
mov ecx, dword ds:[GlobalSecondaryBuffer]
push ecx
mov ecx, [ecx]
call [ecx+0x30]
mov dword ds:[HRESULT], eax
cmp eax, 0x0
je _done
int3
ASSERT()

_done:

mov dword ds:[START_MEM], 0x1 ; see above
_out:

CODE_END

; iyhh
mov eax, dword ds:[HRESULT]

ret (ArgumentCount * DWORD)