CROSS_COMPILE=arm-linux-gnueabihf-
CC=$(CROSS_COMPILE)gcc
LD=$(CROSS_COMPILE)ld
OBJCOPY=$(CROSS_COMPILE)objcopy

all: l-loader.bin
l-loader.bin: start.S debug.S
	$(CC) -c -o start.o start.S
	$(CC) -c -o debug.o debug.S
	$(LD) -Bstatic -Tl-loader.lds -Ttext 0xf9800800 start.o debug.o -o l-loader
	$(OBJCOPY) --pad-to 0xf9802000 -O binary l-loader temp
	cat temp bl1.bin > temp.bin
	dd if=temp.bin of=l-loader.bin bs=48K count=1 conv=sync

clean:
	rm -f *.o l-loader l-loader.bin temp.bin temp
