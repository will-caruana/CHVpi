# CHVpi

How to set up the Pi for the CHV:

1. Login to your Rasberry Pi as user pi
2. Execute the following:
```
git clone https://github.com/5hu5ky/CHVpi.git
cd CHVpi
chmod a+x chvpi_init.sh
./chvpi_init.sh
```

Usage: chvpi_init.sh nosdr|sdr

By default chvpi_init.sh does not require any arguments, if you want rtl-sdr tools to be installed run it using the **sdr** parameter...

```./chvpi_init.sh sdr```


Python Example to be loaded onto the Pi:\
CanFuzz_SIDs.py\
CanFuzz_TesterPresent.py\
controllerareanetwork.py\
iso14229.py\
