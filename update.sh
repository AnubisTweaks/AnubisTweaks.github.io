dpkg-scanpackages -m debs > Packages
rm -f Packages.bz2
bzip2 -c9 Packages > Packages.bz2
git add debs Packages.bz2 depictions
git commit -m "update"
git push
