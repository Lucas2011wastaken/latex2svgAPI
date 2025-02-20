# latex2svgAPI
a simple python script that allows user to compile LaTeX and get a SVG output via API.

recommended platform: Linux
> for its fast LaTeX compilation

**IMPORTANT: THIS API REQUIRES THE FOLLOWING APPLICATIONS INSTALLED ON THE SERVER**
- [xelatex](https://tug.org/texlive/)
- [pdf2svg](https://github.com/dawbarton/pdf2svg)


# calling the API

method: GET

|Parameter|type|comments|
|:--:|:--:|:---|
|`token`|str|a string to distinguish diffrent users, plz configure it in `user.json`|
|`latex`|str|the code you need to compile, plz carefully check if you need to warp it with `$`(e.g. `\LaTeX`don't required `$`)|
|`border`|float|(OPTIONAL)the border control for standalone, 0 by default|
|`twicecompile`|bool|(OPTIONAL)for some circumstances that requires a second compilation. (e.g. macro, polymer) False by default|

## result:

### success:
ˋlatexout.svg`

### failure:
- `{"error": "Unauthorised"}`: token not recoganised. plz configure in `user.json`.
- `{"error": "InsufficientUsage"}`: the token you were using is out of usage. plz re-configure `maxusage` in `user.json`.
- `{"error": "LaTeXCompileFault"}`: your LaTeX sytnex has something wrong. details are given below.
- `{"error": "File not found"}`:cannot found svg to return.plz check your pdf2svg installation.
# deploy

install fastapi and unvicorn:

```bash
pip install fastapi
pip install unvicorn
```

run the script:

```bash
uvicorn main:app --reload
```
configure the `user.json` file. example is given below:

```json
{
    "gzgz": {
        "currentusage": 26,
        "maxusage": -1
    }
}
```

"gzgz" is where your token goes.

# undone checklist

- [x] CompileTwice: for some circumstances that requires a second compilation. (e.g. macro, polymer)
- [x] RecordUsage: record the usage for users
