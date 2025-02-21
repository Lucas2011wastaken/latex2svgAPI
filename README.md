# latex2svgAPI
a simple python script that allows user to compile LaTeX and get a SVG output via API.

recommended platform: Linux
> for its fast LaTeX compilation

used package: chemfig,mhchem,ctex,tikz

**IMPORTANT: THIS API REQUIRES THE FOLLOWING APPLICATIONS INSTALLED ON THE SERVER**
- [xelatex](https://tug.org/texlive/)
- [pdf2svg](https://github.com/dawbarton/pdf2svg)


# calling the API

method: GET
port:4000

|Parameter|type|comments|
|:--:|:--:|:---|
|`token`|str|a string to distinguish diffrent users, plz configure it in `user.json`|
|`latex`|str|the code you need to compile, plz carefully check if you need to warp it with `$`(e.g. `\LaTeX`don't required `$`)|
|`border`|float|(OPTIONAL)the border control for standalone, 0 by default|
|`twicecompile`|bool|(OPTIONAL)for some circumstances that requires a second compilation. (e.g. macro, polymer) False by default|
|`superiorcacheid`|str|(OPTIONAL)the unique "name" to the SVG when caching the superior users' SVG file.(explanation witten bellow)|

## result:

### success:
`latexout.svg`

### failure:
- `{"error": "Unauthorised"}`: token not recoganised. plz configure in `user.json`.
- `{"error": "InsufficientUsage"}`: the token you were using is out of usage. plz re-configure `maxusage` in `user.json`.
- `{"error": "LaTeXCompileFault"}`: your LaTeX sytnex has something wrong. details are given below.
- `{"error": "File not found"}`:cannot found svg to return.plz check your pdf2svg installation.

## examples

```
https://www.example.com:4000/?token=gzgz&twicecompile=true&latex=$ \ce{Z }\left[\chemfig{[,0.6] W(-[:120]M)(-[4]M)(-[:-120]M)-[@{left,0.5}:-30,0.8]W(-[2]M)(-[6]M)-[@{right,0.5}:30,0.8]X-[2]Y(=[0]X)(=[4]X)-[2]X}\right]^- \polymerdelim[delimiters={()},height=2pt, depth=5pt, indice=n]{left}{right} $

```

result:
![](https://raw.githubusercontent.com/Lucas2011wastaken/latex2svgAPI/refs/heads/main/cache/1740027670.3095944/latexoutput.svg)

```
https://www.example.com:4000/?token=gzgz
```

result:
![](https://raw.githubusercontent.com/Lucas2011wastaken/latex2svgAPI/refs/heads/main/cache/1740027512.4471781/latexoutput.svg)
# deploy

install fastapi and unvicorn:

```bash
pip install fastapi
pip install unvicorn
```

configure the `user.json` file. example is given below:

```json
{
    "gzgz": {
        "currentusage": 49,
        "maxusage": -1,
        "superior": true
    }
}
```

"gzgz" is where the token goes.

if a user is configured as a superior in `user.json`, the user can access to an extra cache zone, where the output SVG is cached specifically. So that when user call with the same `superiorcacheid` once again, the API will return the superior cache directly to optimise latency issues.


run the script:

```bash
python3 main.py
```

# undone checklist

- [x] CompileTwice: for some circumstances that requires a second compilation. (e.g. macro, polymer)
- [x] RecordUsage: record the usage for users
- [ ] ToDoList: a todo list was left behind in school lol