CROSS_COMPILE=arm-linux-gnueabihf-
CC=$(CROSS_COMPILE)gcc
LD=$(CROSS_COMPILE)ld
OBJCOPY=$(CROSS_COMPILE)objcopy

all: l-loader.bin
l-loader.bin: start.S debug.S
	$(CC) -c -o start.o start.S
	$(CC) -c -o debug.o debug.S
	$(LD) -Bstatic -Tl-loader.lds -Ttext 0xf9800800 start.o debug.o -o loader
	$(OBJCOPY) -O binary loader temp
	python gen_loader.py -o l-loader.bin --img_loader=temp --img_bl1=bl1.bin
	python gen_loader.py -o bios.bin --img_prm_ptable=prm_ptable.img --img_sec_ptable=sec_ptable.img --img_fip=fip.bin

clean:
	rm -f *.o loader l-loader.bin temp
