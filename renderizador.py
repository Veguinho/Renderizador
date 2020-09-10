# Desenvolvido por: Luciano Soares <lpsoares@insper.edu.br>
# Disciplina: Computação Gráfica
# Data: 28 de Agosto de 2020

import argparse     # Para tratar os parâmetros da linha de comando
import x3d          # Faz a leitura do arquivo X3D, gera o grafo de cena e faz traversal
import interface    # Janela de visualização baseada no Matplotlib
import gpu          # Simula os recursos de uma GPU
import numpy as np  #Para calculos matematicos

##### ADAPTED CODE FROM: https://stackoverflow.com/questions/2049582/how-to-determine-if-a-point-is-in-a-2d-triangle #####
#Checks the sign of the dot product between point and triangle edge
def checkSign(pt, v0, v1):
    return (pt[0] - v1[0]) * (v0[1] - v1[1]) - (v0[0] - v1[0]) * (pt[1] - v1[1])

#Checks if point is inside triangle
def isInside(vertices, point):
    v0 = [vertices[0], vertices[1]]
    v1 = [vertices[2], vertices[3]]
    v2 = [vertices[4], vertices[5]]

    d1 = checkSign(point, v0, v1)
    d2 = checkSign(point, v1, v2)
    d3 = checkSign(point, v2, v0)

    has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
    has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

    return not(has_neg and has_pos)

##################################################################################################################


#IMPLEMENTATION OF BRESENHAM'S ALGORITHM FROM: https://github.com/encukou/bresenham
def bresenham(x0, y0, x1, y1):
    """Yield integer coordinates on the line from (x0, y0) to (x1, y1).
    Input coordinates should be integers.
    The result will contain both the start and the end point.
    """
    dx = x1 - x0
    dy = y1 - y0

    xsign = 1 if dx > 0 else -1
    ysign = 1 if dy > 0 else -1

    dx = abs(dx)
    dy = abs(dy)

    if dx > dy:
        xx, xy, yx, yy = xsign, 0, 0, ysign
    else:
        dx, dy = dy, dx
        xx, xy, yx, yy = 0, ysign, xsign, 0

    D = 2*dy - dx
    y = 0

    for x in range(dx + 1):
        yield x0 + x*xx + y*yx, y0 + x*xy + y*yy
        if D >= 0:
            y += 1
            D -= 2*dx
        D += 2*dy

def polypoint2D(point, color):
    """ Função usada para renderizar Polypoint2D. """
    p=0
    while p < len(point):
        gpu.GPU.set_pixel(int(point[p]), int(point[p+1]), int(255*color[0]), int(255*color[1]), int(255*color[2])) # altera um pixel da imagem
        p+=2
    # cuidado com as cores, o X3D especifica de (0,1) e o Framebuffer de (0,255)

def polyline2D(lineSegments, color):
    """ Função usada para renderizar Polyline2D. """
    # x = gpu.GPU.width//2
    # y = gpu.GPU.height//2
    line_coords = list(bresenham(int(lineSegments[0]), int(lineSegments[1]), int(lineSegments[2]), int(lineSegments[3]))) #Faz cálculo de quais pixeis irão ser pintados baseados no algoritmo de Bresenham e salva num vetor
    for point in line_coords:
        gpu.GPU.set_pixel(int(point[0]), int(point[1]), int(255*color[0]), int(255*color[1]), int(255*color[2])) # altera um pixel da imagem

def triangleSet2D(vertices, color):
    """ Função usada para renderizar TriangleSet2D. """
    for l in range(0,LARGURA):
        for a in range(0,ALTURA):
            #Multisampling for anti-aliasing (4XAA)
            multiplier0 = isInside(vertices, [l+0.33,a+0.33])
            multiplier1 = isInside(vertices, [l+0.33,a+0.66])
            multiplier2 = isInside(vertices, [l+0.66,a+0.33])
            multiplier3 = isInside(vertices, [l+0.66,a+0.66])
            #Final multiplier checks which parts of the pixel are covered by triangle
            fm = 0.25*multiplier0 + 0.25*multiplier1 + 0.25*multiplier2 + 0.25*multiplier3
            if fm > 0:
                gpu.GPU.set_pixel(l, a, 255*fm*color[0], 255*fm*color[1], 255*fm*color[2]) # altera um pixel da imagem

def triangleSet(point, color):
    """ Função usada para renderizar TriangleSet. """
    print("TriangleSet : pontos = {0}".format(point)) # imprime no terminal pontos

def viewpoint(position, orientation, fieldOfView):
    """ Função usada para renderizar (na verdade coletar os dados) de Viewpoint. """
    print("Viewpoint : position = {0}, orientation = {0}, fieldOfView = {0}".format(position, orientation, fieldOfView)) # imprime no terminal

def transform(translation, scale, rotation):
    """ Função usada para renderizar (na verdade coletar os dados) de Transform. """
    print("Transform : ", end = '')
    if translation:
        print("translation = {0} ".format(translation), end = '') # imprime no terminal
    if scale:
        print("scale = {0} ".format(scale), end = '') # imprime no terminal
    if rotation:
        print("rotation = {0} ".format(rotation), end = '') # imprime no terminal
    print("")

def triangleStripSet(point, stripCount, color):
    """ Função usada para renderizar TriangleStripSet. """
    print("TriangleStripSet : pontos = {0} ".format(point), end = '') # imprime no terminal pontos
    for i, strip in enumerate(stripCount):
        print("strip[{0}] = {1} ".format(i, strip), end = '') # imprime no terminal
    print("")

def indexedTriangleStripSet(point, index, color):
    """ Função usada para renderizar IndexedTriangleStripSet. """
    print("IndexedTriangleStripSet : pontos = {0}, index = {1}".format(point, index)) # imprime no terminal pontos

def box(size, color):
    """ Função usada para renderizar Boxes. """
    print("Box : size = {0}".format(size)) # imprime no terminal pontos


LARGURA = 30
ALTURA = 20

if __name__ == '__main__':

    # Valores padrão da aplicação
    width = LARGURA
    height = ALTURA
    x3d_file = "exemplo4.x3d"
    image_file = "tela.png"

    # Tratando entrada de parâmetro
    parser = argparse.ArgumentParser(add_help=False)   # parser para linha de comando
    parser.add_argument("-i", "--input", help="arquivo X3D de entrada")
    parser.add_argument("-o", "--output", help="arquivo 2D de saída (imagem)")
    parser.add_argument("-w", "--width", help="resolução horizonta", type=int)
    parser.add_argument("-h", "--height", help="resolução vertical", type=int)
    parser.add_argument("-q", "--quiet", help="não exibe janela de visualização", action='store_true')
    args = parser.parse_args() # parse the arguments
    if args.input: x3d_file = args.input
    if args.output: image_file = args.output
    if args.width: width = args.width
    if args.height: height = args.height

    # Iniciando simulação de GPU
    gpu.GPU(width, height, image_file)

    # Abre arquivo X3D
    scene = x3d.X3D(x3d_file)
    scene.set_resolution(width, height)

    # funções que irão fazer o rendering
    x3d.X3D.render["Polypoint2D"] = polypoint2D
    x3d.X3D.render["Polyline2D"] = polyline2D
    x3d.X3D.render["TriangleSet2D"] = triangleSet2D
    x3d.X3D.render["TriangleSet"] = triangleSet
    x3d.X3D.render["Viewpoint"] = viewpoint
    x3d.X3D.render["Transform"] = transform
    x3d.X3D.render["TriangleStripSet"] = triangleStripSet
    x3d.X3D.render["IndexedTriangleStripSet"] = indexedTriangleStripSet
    x3d.X3D.render["Box"] = box

    # Se no modo silencioso não configurar janela de visualização
    if not args.quiet:
        window = interface.Interface(width, height)
        scene.set_preview(window)

    scene.parse() # faz o traversal no grafo de cena

    # Se no modo silencioso salvar imagem e não mostrar janela de visualização
    if args.quiet:
        gpu.GPU.save_image() # Salva imagem em arquivo
    else:
        window.image_saver = gpu.GPU.save_image # pasa a função para salvar imagens
        window.preview(gpu.GPU._frame_buffer) # mostra janela de visualização
