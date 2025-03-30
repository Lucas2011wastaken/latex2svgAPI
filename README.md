# latex2svgAPI
a simple python script that allows user to compile LaTeX and get a SVG output via API.

recommended platform: Linux
> *Note:* for its fast LaTeX compilation

used package: chemfig,mhchem,ctex,tikz

# Features

## Compile using original LaTeX installation

By calling the pre-installed LaTeX installation(XeLaTeX by defalt), it will return exactly the most "authentic" LaTeX, supporting `tikz`, `chemfig` and so on.

Also, it will provide a detailed error output so that you can correct your typos accordingly.

## Chinese support

Chinese characters are supported, as long as you put them in the right place. E.g. `$\text{中文}$`

## Precise and customisable Edge cutting

With the use of Standalone DocClass, the white margin is removed atomantically. You can also customize it using `border=`.

## Defined macro support

In some circumstances, when you introduced a marcro, it is likely you'll need a second compilation. You can achieve this using `twicecompile=true`.

## Superior cache

Extra cache zone for certain user(s). By specifying a `superiorcacheid`, it will save the latest success output automatically, and provide the result directly to users next time they request for the exact same thing(aka. identical `superiorcacheid`).

Superiorcache can be managed(list, delete) easily. See also [Calling the API -- superiorcache](#superiorcache).

`superiorcacheid` can't contain illegal characters(i.e. `/?.\@#$&()|:*;<>"`).

You can access to superiorcache without leaking your token and superiorcacheid by calling the API directly using the UID of the cached SVG, see also [Calling the API -- superiorcache](#superiorcache).

## User control

By configuring in `user.json`, you can run your API for certain users, and limit their usage.

if a user is configured as a superior in `user.json`, the user can access to an extra cache zone, where the output SVG is cached specifically. So that when user call with the same `superiorcacheid` once again, the API will return the superior cache directly to optimize latency issues.

# Calling the API

port:4000

## `"/"`: 

method: GET

|Parameter|type|comments|
|:--:|:--:|:---|
|`token`|str|a string to distinguish different users, plz configure it in `user.json`.|
|`latex`|str|(OPTIONAL)the code you need to compile, plz carefully check if you need to wrap it with `$`(e.g. `\LaTeX`don't required `$`), `\LaTeX` by default.|
|`border`|float|(OPTIONAL)the border control for standalone, 0 by default. e.g. `border=5.0`|
|`twicecompile`|bool|(OPTIONAL)for some circumstances that requires a second compilation. (e.g. macro, polymer) False by default.|
|`superiorcacheid`|str|(OPTIONAL)the unique "name" to the SVG when caching the superior users' SVG file.(explanation witten bellow)|

### success:

`latexout.svg`

### failure:
- `{"error": "Unauthorised"}`: token not recognised. plz configure in `user.json`.
- `{"error": "InsufficientUsage"}`: the token you were using is out of usage. plz re-configure `maxusage` in `user.json`.
- `{"error": "LaTeXCompileFault"}`: your LaTeX stynex has something wrong. details are given below.
- `{"error": "File not found"}`:cannot found SVG to return.plz check your pdf2svg installation.

### examples

> HTTPS is configured seperately. On the example server, it's enabled.If you don't want to configure a HTTPS(although it's recommended to), replace <code>https</code> with <code>http</code> in the following instead.

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


```
https://www.example.com:4000/?token=gzgz&superiorcacheid=benzene
```

result:

**THIS ONE IS NOT RECOMMENDED TO USE UNLESS YOU KNOW WHAT YOU ARE DOING.** The server will return the superiorcache whose ID is "benzene" IF EXIST. Otherwise it will return ![](https://raw.githubusercontent.com/Lucas2011wastaken/latex2svgAPI/refs/heads/main/cache/1740027512.4471781/latexoutput.svg) caused by the default in put of parameter `latex`.

## `"/superiorcache"`

Operate superiorcache by calling it with query parameters, and access UID superiorcache by calling it with path parameters.

### query parameters

method: GET

|Parameter|type|comments|
|:--:|:--:|:---|
|`token`|str|a string to distinguish different users, plz configure it in `user.json`.|
|`action`|str|`list` or `delete`. `list` will return a table showing all your superiorcache; `delete` is not completed yet. plz stay tuned.|

#### success: `action=list`

List all available superiorchache in a web page.

#### success: `action=delete`

delete a certain superiorcache and return: `{"success": "FileDeleted example.svg"}`

#### failure:
- `{"error": "Unauthorised"}`: token not recognized. plz configure in `user.json`.
- `{"error": "InsufficientUsage"}`: the token you were using is out of usage. plz re-configure `maxusage` in `user.json`.
- `{"error": "InvalidAction"}`: action you requested is not on the support list, plz check your spellings.
- `{"error": "DeletionFailed"}`: can't delete a certain superiorcache, idk why. (maybe permission reason?)
- `{"error": "FileNotFound"}`: the `superiorcacheid` you requested does not exist. plz check your spellings.

### path parameters

access your SVG by passing in UID, for instance:

```
https://www.example.com:4000/superiorcache/d2b521cdad6799c342414a76eb1f06eb.svg
```
`d2b521cdad6799c342414a76eb1f06eb` is the UID of the SVG image, you can acquire it in the SVG list(replace `gzgz` with your own token):

```
https://www.example.com:4000/superiorcache?token=gzgz&action=list
```
# deploy

install [xelatex](https://tug.org/texlive/) and [pdf2svg](https://github.com/dawbarton/pdf2svg).

install fastapi and uvicorn:

```bash
pip install fastapi
pip install uvicorn
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

- [ ] AddCESupport: support ce when modifying superiorcache.
- [ ] ~~TryUserEndCache: it seems that you can do this... I'm not sure. Require more ivestigation.~~
