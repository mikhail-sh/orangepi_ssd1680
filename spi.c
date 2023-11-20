/*
   Marko Pinteric 2020
   GPIO communication based on Tiny GPIO Access on http://abyz.me.uk/rpi/pigpio/examples.html

   Create shared object with: gcc -o spi.so -shared -fPIC spi.c
*/

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>
#include <fcntl.h>
#include <stdbool.h> 
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <linux/spi/spidev.h>

/* LOCAL VARIABLES */

int fd_spi;
struct spi_ioc_transfer spi;

/* communication initialised */
bool init_spi=false;


/* SPI METHODS */

/* initialise communications */
/* parameters: SPI bus number, frequency */
int spiInitialise(int dev, uint32_t frequency)
{
   char filename[20];

   snprintf(filename, 20, "/dev/spidev%d.1", dev);
   fd_spi = open(filename, O_RDWR);
   if (fd_spi < 0) fprintf(stderr, "Failed to open the spi%d.1 bus\n", dev);

   spi.delay_usecs = 0;
   spi.speed_hz = frequency;
   spi.bits_per_word = 8;
   fprintf(stderr, "Connect to open the spi%d.1 bus\n", dev);
   return(fd_spi);
}

/* write to SPI bus */
void spiWrite(uint8_t data[], int len)
{
  spi.tx_buf =(unsigned long)data;
  spi.rx_buf =(unsigned long)NULL;
  spi.len = len;
  ioctl(fd_spi, SPI_IOC_MESSAGE(1), &spi);
}
