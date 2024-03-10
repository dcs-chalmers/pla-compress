
from compressor import *
from linear import LinearCompressor

def pla2tikzv0(filename, error=0.25):
    datastream = streamfile(filename,1)
    segments = list(LinearCompressor().compress(datastream, error))
    plareconstruct = list(LinearCompressor().gendata(filename, error))
    data = list(streamfile(filename,1))

    yt = -0.5

    print("\\begin{tikzpicture}")
    print("\\node[red, text width=1cm, style={align=center}] at (-0.5, 1.5) {Input Stream};")
    print("\draw[->, thick] (",data[0][0]-1,",",yt,") -- (",
          data[-1][0]+1,",",yt,") node[xshift=0.5cm] {Time};",sep='')
    m = max(y for x,y in data)+1
    print("\draw[->, thick, text width=1cm, style={align=center}] (",data[0][0]-1,",",m,") -- (",
          data[-1][0]+1,",",m,") node[xshift=0.75cm] {Output Stream};", sep='')

    l = 0
    #print(plareconstruct)
    for i in range(len(data)):
        t, y = data[i]
        
        print("\draw (",t,",",yt+0.25,") -- (",t,",",yt-0.25,");",sep='')
        print("\\node[cross, red] at ", (t,y)," {};",sep='')

        if plareconstruct[i][1] is not None and i > 0: # something is reconstructed
            record = segments[l]
            if len(record) == 2:
                print("\\node[rotate=30, anchor=west] at (",t,",",m+0.25,") {$<1,y_{",l+1,"}>$};",sep='')
                print("\draw (",t,",",m-0.25,") -- (",t,",",m+0.25,");",sep='')
            else:   
                print("\\node[rotate=30, anchor=west] at (",t,",",m+0.25,") {$<",record[0],",a_{",l+1,"},b_{",l+1,"}>$};",sep='')
                print("\draw (",t,",",m-0.25,") -- (",t,",",m+0.25,");",sep='')
            l+=1

    i = 0
    for j in range(len(segments)):
        segment = segments[j]
        n = segment[0]
        if len(segment) == 2:
            print("\\node[blue] at ",data[i]," {$\\bullet$};",sep='')
            x, y = data[i][0], data[i][1]
            print("\\node[blue] at ",(x,y)," {$y_{",j+1,"}=","{0:.2f}".format(y),"$};",sep='')
        else:
            n, a, b = segment
            x0, xn = data[i][0], data[i+n-1][0]
            y0, yn = a*x0+b, a*xn+b
            print("\draw[blue] (", x0, ",","{0:.2f}".format(y0),") -- (",xn,",",
                  "{0:.2f}".format(yn),
                  ") node[pos=0.5,sloped,yshift=0.5cm,above] {$a_{",j+1,"}=",
                  "{0:.2f}".format(a),",b_{",j+1,"}=","{0:.2f}".format(b),
                  "$};",sep='')
            for k in range(n):
                x = data[i+k][0]
                y = a*x+b
                print("\\node[blue] at (",x,",","{0:.2f}".format(y),
                      ") {$\\bullet$};",sep='')
                print("\draw ",data[i+k]," -- (",x,",","{0:.2f}".format(y),
                      ");",sep='')

        i += n
    

    print("\end{tikzpicture}")

def pla2tikz(data, segments, plareconstruct, error=0.25, outf=None, name="Input Stream",
             errunit=None, errconvert=1, turnoffsegments=False, font='normalsize',
             maxt=34.75, maxy=2, fprecision=3):
    yt = -0.5
    t0 = data[0][0]
    rescale_t = lambda t : maxt*(t-t0)/(data[-1][0]-t0)
    x0 = rescale_t(data[0][0])-1
    xlast = rescale_t(data[-1][0])+0.5
    xn = rescale_t(data[-1][0])+1

    k = next((i for i in range(len(data)) if plareconstruct[i][1] is not None), len(data)-1)
    xout = rescale_t(data[k][0])-1

    ymax = max(y for x,y in data)
    ymin = min(y for x,y in data)
    rescale_y = lambda y : maxy*(y-ymin)/(ymax-ymin)
    yout = maxy+0.5
    
    output = lambda f : str(round(f,fprecision))
    output2 = lambda f : str(round(f,2))
    
    err = "\\num{{{0:.2E}}}".format(error/errconvert)

    print(f'% global parameters',file=outf)
    print(r'\newcommand\xz{'+output(x0)+'}',file=outf)
    print(r'\newcommand\xn{'+output(xn)+'}',file=outf)
    print(r'\newcommand\xlast{'+output(xlast)+'}',file=outf)
    print(r'\newcommand\yt{'+output(yt)+'}',file=outf)
    print(r'\newcommand\ytb{'+output(yt-0.25)+'}',file=outf)
    print(r'\newcommand\ytt{'+output(yt+0.25)+'}',file=outf)
    print(r'\newcommand\yout{'+output(yout)+'}',file=outf)
    print(r'\newcommand\youtb{'+output(yout-0.25)+'}',file=outf)
    print(r'\newcommand\youtt{'+output(yout+0.25)+'}',file=outf)

    print(f'% some variables for easier modifications',file=outf)
    print(r'\newcommand\T{0}',file=outf)
    print(r'\newcommand\Y{0}',file=outf)

    print("\\begin{tikzpicture}[font=\large]",file=outf)
    
    print("\\node[red, text width=1cm, style={align=center},font=\Large] at (0, 1.5) {",name,"};",sep='',file=outf)
    print("\\node[blue, text width=3.5cm, style={align=center},font=\Large] at (",xlast-2,", 0.75) {Reconstructed ",name," MaxError=$",int(error/errconvert),errunit,"$};",sep='',file=outf)

    print(r"\draw[->] (\xz,\ytb) -- (\xz,\youtt);",file=outf)
    step=(yout-yt)/4
    stepy = (ymax-ymin)/maxy
    for i in range(4):
        print(r"\draw ("+output(x0-0.25)+","+output(yt+i*step)+") -- ("+output(x0)+","+output(yt+i*step)+
              ") node[left, xshift=-0.25cm,font=\Large] {"+output2(stepy*i/errconvert)+errunit+"};",file=outf)
        print(r"\draw ("+output(x0-0.15)+","+output(yt+(i+0.5)*step)+") -- ("
              +output(x0)+","+output(yt+(i+0.5)*step)+");",file=outf)
    print(r"\draw ("+output(x0-0.25)+","+output(yt+4*step)+") -- ("
          +output(x0)+","+output(yt+4*step)+") node[left, xshift=-0.25cm,font=\Large] {"+output2(stepy*4/errconvert)+errunit+"};",file=outf)
    
    print(r"\draw[->, thick] (\xz,\yt) -- (\xn,\yt) node[xshift=0.75cm,font=\Large] {Time};",file=outf)    
    print(r"\draw[->, thick, text width=1cm, style={align=center}, blue] (",output(xout)
          ,r",\yout) -- (\xn,\yout) node[xshift=1cm,text width=2cm,font=\Large] {Output Stream};", sep='',file=outf)

    l = 0
    for i in range(len(data)):
        t, y = data[i]
        t = rescale_t(t)
        y = rescale_y(y)
        print(f'% input datapoint {data[i]}',file=outf)
        print(r'\renewcommand\T{'+output(t)+'};',file=outf)
        print(r'\renewcommand\Y{'+output(y)+'};',file=outf)
        print(r"\draw (\T,\ytb) -- (\T,\ytt);",file=outf)
        print(r"\node[cross, red] at (\T,\Y) {};",sep='',file=outf)

        if plareconstruct[i][1] is not None and i > 0: # something is reconstructed
            record = segments[l]
            l+=1
            n=record[0]
            if len(record) == 2:
                print("\\node[rotate=30, anchor=west, blue] at (\T,\youtt) {$\langle",n,",y_{",l,"}\\rangle$};",sep="",file=outf)
            elif not turnoffsegments:   
                print("\\node[rotate=30, anchor=west, blue] at (\T,\youtt) {$\langle",n,",a_{",l,"},b_{",l,"}\\rangle$};",sep="",file=outf)
            print(r"\draw[blue] (\T,\youtb) -- (\T,\youtt);",file=outf)

    #flush 1 extra segments at the end
    record = segments[l]
    l+=1
    n=record[0]
    if len(record) == 2:
        print("\\node[rotate=30, anchor=west, blue] at (\\xlast,\\youtt) {$\\langle",n,",y_{",l,"}\\rangle$};",sep="",file=outf)
    elif not turnoffsegments:   
        print("\\node[rotate=30, anchor=west, blue] at (\\xlast,\\youtt) {$\\langle",n,",a_{",l,"},b_{",l,"}\\rangle$};",sep="",file=outf)
    print(r"\draw[blue] (\xlast,\youtb) -- (\xlast,\youtt);",file=outf)
    

    i = 0
    for j in range(len(segments)):
        segment = segments[j]
        n = segment[0]
        
        if len(segment) == 2:
            t, y = data[i]
            t = rescale_t(t)
            y = rescale_y(y)
            print(f'% reconstructed singleton {data[i]}',file=outf)
            print(r'\renewcommand\T{'+output(t)+'};',file=outf)
            print(r'\renewcommand\Y{'+output(y)+'};',file=outf)
            print(r"\node[blue] at (\T,\Y) {$\square$};",sep='',file=outf)
            #print("\\node[blue] at (\T,\Y) {$y_{",j,"}=","{0:.4f}".format(data[i][1]),"$};",sep='',file=outf)
            print("\\node[blue, above=3pt] at (\T,\Y) {$y_{",j+1,"}$};",sep='',file=outf)
        else:
            n, a, b = segment
            xb, xf = rescale_t(data[i][0]), rescale_t(data[i+n-1][0])
            yb, yf = rescale_y(a*data[i][0]+b), rescale_y(a*data[i+n-1][0]+b)
            
            #print(r"\draw[blue] ("+output(xb)+","+output(yb)+") -- ("+output(xf)+","+output(yf)+") node[pos=0.5,sloped,yshift=0.5cm,above] {$a_{",j+1,"}=",
            #      "\\num{{{0:.2E}}}".format(a),",b_{",j+1,"}=","\\num{{{0:.2E}}}".format(b),"$};",sep='',file=outf)

            if not turnoffsegments:
                print("\\draw[blue] ("+output(xb)+","+output(yb)+") -- ("+output(xf)+","+output(yf)
                  +") node[pos=0.5,sloped,yshift=0.05cm,above] {$(a_{",j+1,"},b_{",j+1,"})$};",sep='',file=outf)
            else:
                print("\\draw[blue] ("+output(xb)+","+output(yb)+") -- ("+output(xf)+","+output(yf)+");",sep='',file=outf)
            
            for k in range(n):
                rt = data[i+k][0]
                ry = a*rt+b
                t = rescale_t(rt)
                y = rescale_y(ry)
                y_ori = rescale_y(data[i+k][1])
                print(f'% reconstructed segment approximation {(rt,ry)}',file=outf)
                print(r'\renewcommand\T{'+output(t)+'};',file=outf)
                print(r'\renewcommand\Y{'+output(y)+'};',file=outf)
                print(r"\node[blue] at (\T,\Y) {{\boldmath$\cdot$}};",file=outf)
                print("\draw[green] (\T,"+output(y_ori)+") -- (\T,\Y);",file=outf)

        i += n

    print("\end{tikzpicture}",file=outf)
    
def csv2pdf(axis=1,error=0.1,name='Input',errunit=None,errconvert=1):
    with open('out.tex','w') as outf:
        print(r"\documentclass{standalone}",file=outf)
        print(r"\usepackage{amssymb}",file=outf)
        print(r"\usepackage{siunitx}",file=outf)
        print(r"\usepackage{tikz}",file=outf)
        print(r"\usetikzlibrary{shapes.misc}",file=outf)
        print(r"\tikzset{cross/.style={cross out, draw=black, fill=none, minimum size=2*(#1-\pgflinewidth), inner sep=0pt, outer sep=0pt}, cross/.default={2pt}, extended line/.style={shorten >=-#1,shorten <=-#1}, extended line/.default=1cm, one end extended/.style={shorten >=-#1},one end extended/.default=1cm}",file=outf)
        print(r"\begin{document}",file=outf)
        filename = 'zoom.csv'
        data = list(streamfile(filename, axis))
        segments = list(LinearCompressor().compress(streamfile(filename, axis), error))
        plareconstruct = list(LinearCompressor().genplastream(streamfile(filename, axis), error, streamtimefile(filename)))
        pla2tikz(data,segments,plareconstruct,error,outf,name,errunit,errconvert)
        print(r"\end{document}",file=outf)
    import os
    os.system("pdflatex out.tex")

def csv2pdftime(axis=0,error=0,name='Input',errunit=None,errconvert=1):
    with open('out.tex','w') as outf:
        print(r"\documentclass{standalone}",file=outf)
        print(r"\usepackage{amssymb}",file=outf)
        print(r"\usepackage{siunitx}",file=outf)
        print(r"\usepackage{tikz}",file=outf)
        print(r"\usetikzlibrary{shapes.misc}",file=outf)
        print(r"\tikzset{cross/.style={cross out, draw=black, fill=none, minimum size=2*(#1-\pgflinewidth), inner sep=0pt, outer sep=0pt}, cross/.default={2pt}, extended line/.style={shorten >=-#1,shorten <=-#1}, extended line/.default=1cm, one end extended/.style={shorten >=-#1},one end extended/.default=1cm}",file=outf)
        print(r"\begin{document}",file=outf)
        filename = 'zoom.csv'
        segments = list(LinearCompressor().compress(streamfile(filename, axis), error))
        plareconstruct = list(LinearCompressor().genplastream(streamfile(filename,axis), error, logicaltimes(streamfile(filename,axis))))
        data = list(streamfile(filename, axis))
        pla2tikz(data,segments,plareconstruct,error,outf,name,errunit,errconvert,True)
        print(r"\end{document}",file=outf)
    import os
    os.system("pdflatex out.tex")

terror=0
lat1m=0.0000900835
lat10m=0.000900835
lon1m=0.0001171234
lon10m=0.001171234

#csv2pdf(1,laterror,'Latitude')
#>>> csv2pdf(1,lat10m,'Latitude','10m',lat1m)
#>>> csv2pdf(2,lon10m,'Longitude','10m',lon1m)
#csv2pdftime(0,0,'Timestamps','s')

##>>> csv2pdf(2,lon10m,'Longitude','m',lon1m)
##>>> csv2pdftime(0,0,'Timestamps','s')
##>>> csv2pdf(1,lat10m,'Latitude','1',lat1m)
