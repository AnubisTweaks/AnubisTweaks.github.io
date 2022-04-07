cp Base Release
packages_size=$(ls -l Packages | awk '{print $5,$9}')
packages_md5=$(md5sum Packages | awk '{print $1}')
packages_sha256=$(sha256sum Packages | awk '{print $1}')
packagesbz2_size=$(ls -l Packages.bz2 | awk '{print $5,$9}')
packagesbz2_md5=$(md5sum Packages.bz2 | awk '{print $1}')
packagesbz2_sha256=$(sha256sum Packages.bz2 | awk '{print $1}')
packagesgz_size=$(ls -l Packages.gz | awk '{print $5,$9}')
packagesgz_md5=$(md5sum Packages.gz | awk '{print $1}')
packagesgz_sha256=$(sha256sum Packages.gz | awk '{print $1}')
packageszst_size=$(ls -l Packages.zst | awk '{print $5,$9}')
packageszst_md5=$(md5sum Packages.zst | awk '{print $1}')
packageszst_sha256=$(sha256sum Packages.zst | awk '{print $1}')
echo "MD5Sum:" >> Release
echo " $packages_md5 $packages_size" >> Release
echo " $packagesbz2_md5 $packagesbz2_size" >> Release
echo " $packagesgz_md5 $packagesgz_size" >> Release
echo " $packageszst_md5 $packageszst_size" >> Release
echo "SHA256:" >> Release
echo " $packages_sha256 $packages_size" >> Release
echo " $packagesbz2_sha256 $packagesbz2_size" >> Release
echo " $packagesgz_sha256 $packagesgz_size" >> Release
echo " $packageszst_sha256 $packageszst_size" >> Release
echo "Done"
