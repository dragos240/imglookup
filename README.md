# imglookup

imglookup is a local image indexer that uses the saucenao API to find matching images, then downloading the tags from the source booru (currently only e621)

```
usage: imglookup.py [-h] [-s] [--saucenao SAUCENAO] [--e621 E621] [-v] path

positional arguments:
  path                 Path(s) to image(s) (use empty string if debugging)

optional arguments:
  -h, --help           show this help message and exit
  -s, --store-json     Saves JSON responses from APIs
  --saucenao SAUCENAO  Specify saucenao JSON file to parse
  --e621 E621          Specify e621 JSON file to parse
  -v, --verbose        Prints out more verbose messages for debugging
```