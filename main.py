from fastapi import FastAPI
from fastapi.responses import FileResponse
import os
import time

UserToken = ["gzgz"]

app = FastAPI()

@app.get("/")
async def main(token:str = "null",twisecomplie:bool = False,latex:str = "LaTeX",border:float = 0):

    # 检查用户是否注册
    global UserToken
    if not token in UserToken:
        return {"error": "Unauthorised"}
    
    # 创建一个临时工作文件夹
    current_folder = "cache/" + str(time.time())
    os.system("mkdir " + current_folder)

    # 处理用户的latex、添加最小工作示例、保存到input.tex
    latexinput = "\\documentclass[10pt]{standalone}\n\\usepackage{tikz}\n\\usepackage{chemfig}\n\\usepackage[UTF8]{ctex}\n\\usepackage[version=4]{mhchem}\n\\usetikzlibrary{intersections,calc,backgrounds,knots}\n\\standaloneconfig{border=" + str(border) + "}\n\\begin{document}\n\n$\n" + latex + "\n$\n\n\\end{document}"

    os.system("touch " + current_folder + "/latexinput.tex")

    with open(current_folder + "/latexinput.tex", "w") as file:
        file.write(latexinput)

    # 调用xelatex进行编译得到pdf
    os.system("xelatex -output-directory=" + current_folder + " " + current_folder + "/latexinput.tex")

    # 调用pdf2svg
    os.system("pdf2svg " + current_folder + "/latexinput.pdf" + " " + current_folder + "/latexoutput.svg")

    # 输出svg
    output_path = current_folder + "/latexoutput.svg"
    if not os.path.isfile(output_path):
        return {"error": "File not found"}
    return FileResponse(output_path, media_type="image/svg+xml")

# 启动 FastAPI 应用程序
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)