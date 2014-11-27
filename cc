#rm -f *.o lboot lboot.bin
#arm-linux-gnueabihf-gcc -c start.S
#arm-linux-gnueabihf-gcc -c debug.S
#arm-linux-gnueabihf-ld -o lboot -T lboot.lds start.o debug.o

#arm-linux-gnueabihf-objcopy -I elf32-littlearm -O binary lboot lboot.bin

make clean
make PLAT=lcb
