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

class Matrix:
    def __init__(self):
        self.matrix = np.array([[1.0,0,0,0],
                                [0,1.0,0,0],
                                [0,0,1.0,0],
                                [0,0,0,1.0]])

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
    # Nessa função você receberá pontos no parâmetro point, esses pontos são uma lista
    # de pontos x, y, e z sempre na ordem. Assim point[0] é o valor da coordenada x do
    # primeiro ponto, point[1] o valor y do primeiro ponto, point[2] o valor z da 
    # coordenada z do primeiro ponto. Já point[3] é a coordenada x do segundo ponto e
    # assim por diante.
    # No TriangleSet os triângulos são informados individualmente, assim os três
    # primeiros pontos definem um triângulo, os três próximos pontos definem um novo
    # triângulo, e assim por diante.
    
    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    print("TriangleSet : pontos = {0}".format(point)) # imprime no terminal pontos

def viewpoint(position, orientation, fieldOfView): #camera
    """ Função usada para renderizar (na verdade coletar os dados) de Viewpoint. """
    look_at_matrix.matrix = np.array([[1.0,0,0,0],
                                      [0,1.0,0,0],
                                      [0,0,1.0,0],
                                      [0,0,0,1.0]])
                                      
    # orientation_matrix = np.array([[1.0,0,0,0],
    #                                [0,1.0,0,0],
    #                                [0,0,1.0,0],
    #                                [0,0,0,1.0]])

    top = NEAR * np.tan(fieldOfView)
    right = top * (LARGURA/ALTURA)

    perspective_matrix = np.array([[NEAR/right,0,0,0],
                                  [0,NEAR/top,0,0],
                                  [0,0,-(FAR+NEAR)/(FAR-NEAR),-2*(FAR*NEAR)/(FAR-NEAR)],
                                  [0,0,-1.0,0]])

    position_matrix = np.array([[1.0,0,0,-position[0]],
                                [0,1.0,0,-position[1]],
                                [0,0,1.0,-position[2]],
                                [0,0,0,1.0]])

    look_at_matrix.matrix = perspective_matrix * position_matrix

    print("Viewpoint : position = {0}, orientation = {1}, fieldOfView = {2}".format(position, orientation, fieldOfView)) # imprime no terminal

def transform(translation, scale, rotation): #objeto -> Pegar as transformacoes em forma de matriz e multiplicar todas elas para obter uma matriz só de transformação
    """ Função usada para renderizar (na verdade coletar os dados) de Transform. """
    op_stack = []
    transform_matrix.matrix = np.array([[1.0,0,0,0],
                                        [0,1.0,0,0],
                                        [0,0,1.0,0],
                                        [0,0,0,1.0]])
    print("Transform : ", end = '')
    if translation:
        op_stack.append(np.array([[1.0,0,0,translation[0]],
                                  [0,1.0,0,translation[1]],
                                  [0,0,1.0,translation[2]],
                                  [0,0,0,1.0]]))
        #print("translation = {0} ".format(translation), end = '') # imprime no terminal
    if scale:
        op_stack.append(np.array([[scale[0],0,0,0],
                                  [0,scale[1],0,0],
                                  [0,0,scale[2],0],
                                  [0,0,0,1]]))
        #print("scale = {0} ".format(scale), end = '') # imprime no terminal
    if rotation:
        if rotation[0]:
            op_stack.append(np.array([[1.0,0,0,0],
                                      [0,np.cos(rotation[3]),-np.sin(rotation[3]),0],
                                      [0,np.sin(rotation[3]),np.cos(rotation[3]),0],
                                      [0,0,0,1]]))
        if rotation[1]:
            op_stack.append(np.array([[np.cos(rotation[3]),0,np.sin(rotation[3]),0],
                                      [0,1.0,0,0],
                                      [-np.sin(rotation[3]),0,np.cos(rotation[3]),0],
                                      [0,0,0,1.0]]))
        if rotation[2]:
            op_stack.append(np.array([[np.cos(rotation[3]),-np.sin(rotation[3]),0,0],
                                      [np.sin(rotation[3]),np.cos(rotation[3]),0,0],
                                      [0,0,1.0,0],
                                      [0,0,0,1.0]]))
        #print("rotation = {0} ".format(rotation), end = '') # imprime no terminal
    while(op_stack): #Faz as operações de transformação na ordem certa
        transform_matrix.matrix *= op_stack.pop()
    #print("FINAL transform_matrix")
    #print(transform_matrix)

def _transform():
    """ Função usada para renderizar (na verdade coletar os dados) de Transform. """
    # A função _transform será chamada quando se sair em um nó X3D do tipo Transform do
    # grafo de cena. Não são passados valores, porém quando se sai de um nó transform se
    # deverá recuperar a matriz de transformação dos modelos do mundo da estrutura de
    # pilha implementada.

    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    print("Saindo de Transform")

def triangleStripSet(point, stripCount, color):
    """ Função usada para renderizar TriangleStripSet. """
    # A função triangleStripSet é usada para desenhar tiras de triângulos interconectados,
    # você receberá as coordenadas dos pontos no parâmetro point, esses pontos são uma
    # lista de pontos x, y, e z sempre na ordem. Assim point[0] é o valor da coordenada x
    # do primeiro ponto, point[1] o valor y do primeiro ponto, point[2] o valor z da
    # coordenada z do primeiro ponto. Já point[3] é a coordenada x do segundo ponto e assim
    # por diante. No TriangleStripSet a quantidade de vértices a serem usados é informado
    # em uma lista chamada stripCount (perceba que é uma lista).

    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    print("TriangleStripSet : pontos = {0} ".format(point), end = '') # imprime no terminal pontos
    for i, strip in enumerate(stripCount):
        print("strip[{0}] = {1} ".format(i, strip), end = '') # imprime no terminal
    print("")

def indexedTriangleStripSet(point, index, color):
    """ Função usada para renderizar IndexedTriangleStripSet. """
    # A função indexedTriangleStripSet é usada para desenhar tiras de triângulos
    # interconectados, você receberá as coordenadas dos pontos no parâmetro point, esses
    # pontos são uma lista de pontos x, y, e z sempre na ordem. Assim point[0] é o valor
    # da coordenada x do primeiro ponto, point[1] o valor y do primeiro ponto, point[2]
    # o valor z da coordenada z do primeiro ponto. Já point[3] é a coordenada x do
    # segundo ponto e assim por diante. No IndexedTriangleStripSet uma lista informando
    # como conectar os vértices é informada em index, o valor -1 indica que a lista
    # acabou. A ordem de conexão será de 3 em 3 pulando um índice. Por exemplo: o
    # primeiro triângulo será com os vértices 0, 1 e 2, depois serão os vértices 1, 2 e 3,
    # depois 2, 3 e 4, e assim por diante.
    
    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    print("IndexedTriangleStripSet : pontos = {0}, index = {1}".format(point, index)) # imprime no terminal pontos

def box(size, color):
    """ Função usada para renderizar Boxes. """
    # A função box é usada para desenhar paralelepípedos na cena. O Box é centrada no
    # (0, 0, 0) no sistema de coordenadas local e alinhado com os eixos de coordenadas
    # locais. O argumento size especifica as extensões da caixa ao longo dos eixos X, Y
    # e Z, respectivamente, e cada valor do tamanho deve ser maior que zero. Para desenha
    # essa caixa você vai provavelmente querer tesselar ela em triângulos, para isso
    # encontre os vértices e defina os triângulos.

    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    print("Box : size = {0}".format(size)) # imprime no terminal pontos


LARGURA = 30
ALTURA = 20
NEAR = 0.5
FAR = 100.0

if __name__ == '__main__':

    transform_matrix = Matrix()
    look_at_matrix = Matrix()

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
    x3d.X3D.render["_Transform"] = _transform
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
