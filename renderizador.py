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
    triangles = []

    for p in range(len(point)):
        if p%9 == 0:      
            triangle_result = np.matmul(transform_matrix.matrix,np.array([[point[p],point[p+3],point[p+6]], #multiplica a matriz dos pontos pela matriz de transformação
                                                                        [point[p+1],point[p+4],point[p+7]],
                                                                        [point[p+2],point[p+5],point[p+8]],
                                                                        [1.0,1.0,1.0]]))
            triangle_result = np.matmul(look_at_matrix.matrix,triangle_result)#multiplica o resultado pela matriz look at
            triangle_result = np.matmul(perspective_matrix.matrix,triangle_result)#multiplica o resultado pela matriz perspectiva
            if(triangle_result[3][0]>0): #normalização
                triangle_result[:,0] /= triangle_result[3][0]
            if(triangle_result[3][1]>0):
                triangle_result[:,1] /= triangle_result[3][1]
            if(triangle_result[3][2]>0):
                triangle_result[:,2] /= triangle_result[3][2]

            screen_matrix = np.array([[LARGURA/2.0,0,0,LARGURA/2.0],
                                      [0,-ALTURA/2.0,0,ALTURA/2.0],
                                      [0,0,1.0,0],
                                      [0,0,0,1.0]])
            triangles.append(np.matmul(screen_matrix,triangle_result))#faz a adequação da matriz normalizada para os pontos da tela
            
    for t in triangles:
        triangleSet2D([t[0][0],t[1][0],t[0][1],t[1][1],t[0][2],t[1][2]], color) #faz a rasterizaçao da matriz
    

    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    #print("TriangleSet : pontos = {0}".format(point)) # imprime no terminal pontos

def viewpoint(position, orientation, fieldOfView): #camera
    """ Função usada para renderizar (na verdade coletar os dados) de Viewpoint. """
    # Na função de viewpoint você receberá a posição, orientação e campo de visão da
    # câmera virtual. Use esses dados para poder calcular e criar a matriz de projeção
    # perspectiva para poder aplicar nos pontos dos objetos geométricos.

    look_at_matrix.matrix = np.array([[1.0,0,0,0],
                                      [0,1.0,0,0],
                                      [0,0,1.0,0],
                                      [0,0,0,1.0]])
                                      
    orientation_matrix = np.array([[1.0,0,0,0],
                                   [0,1.0,0,0],
                                   [0,0,1.0,0],
                                   [0,0,0,1.0]])

    top = NEAR * np.tan(fieldOfView)
    right = top * (LARGURA/ALTURA)

    perspective_matrix.matrix = np.array([[NEAR/right,0,0,0],
                                  [0,NEAR/top,0,0],
                                  [0,0,-(FAR+NEAR)/(FAR-NEAR),-2*(FAR*NEAR)/(FAR-NEAR)],
                                  [0,0,-1.0,0]])

    position_matrix = np.array([[1.0,0,0,-position[0]],
                                [0,1.0,0,-position[1]],
                                [0,0,1.0,-position[2]],
                                [0,0,0,1.0]])

    look_at_matrix.matrix = np.matmul(orientation_matrix,position_matrix)
    

    #print("Viewpoint : position = {0}, orientation = {1}, fieldOfView = {2}".format(position, orientation, fieldOfView)) # imprime no terminal

def transform(translation, scale, rotation): #objeto -> Pegar as transformacoes em forma de matriz e multiplicar todas elas para obter uma matriz só de transformação
    """ Função usada para renderizar (na verdade coletar os dados) de Transform. """
    # A função transform será chamada quando se entrar em um nó X3D do tipo Transform
    # do grafo de cena. Os valores passados são a escala em um vetor [x, y, z]
    # indicando a escala em cada direção, a translação [x, y, z] nas respectivas
    # coordenadas e finalmente a rotação por [x, y, z, t] sendo definida pela rotação
    # do objeto ao redor do eixo x, y, z por t radianos, seguindo a regra da mão direita.
    # Quando se entrar em um nó transform se deverá salvar a matriz de transformação dos
    # modelos do mundo em alguma estrutura de pilha.

    tmp_stack = []

    tmp_matrix = np.array([[1.0,0,0,0],
                            [0,1.0,0,0],
                            [0,0,1.0,0],
                            [0,0,0,1.0]])
    #print("Transform : ", end = '')
    if scale:
        tmp_stack.append(np.array([[scale[0],0,0,0],
                                  [0,scale[1],0,0],
                                  [0,0,scale[2],0],
                                  [0,0,0,1]]))
        #print("scale = {0} ".format(scale), end = '') # imprime no terminal

    if rotation:
        if rotation[0]:
            tmp_stack.append(np.array([[1.0,0,0,0],
                                      [0,np.cos(rotation[3]),-np.sin(rotation[3]),0],
                                      [0,np.sin(rotation[3]),np.cos(rotation[3]),0],
                                      [0,0,0,1.0]]))
        elif rotation[1]:
            tmp_stack.append(np.array([[np.cos(rotation[3]),0,np.sin(rotation[3]),0],
                                      [0,1.0,0,0],
                                      [-np.sin(rotation[3]),0,np.cos(rotation[3]),0],
                                      [0,0,0,1.0]]))
        elif rotation[2]:
            tmp_stack.append(np.array([[np.cos(rotation[3]),-np.sin(rotation[3]),0,0],
                                      [np.sin(rotation[3]),np.cos(rotation[3]),0,0],
                                      [0,0,1.0,0],
                                      [0,0,0,1.0]]))
        #print("rotation = {0} ".format(rotation), end = '') # imprime no terminal

    if translation:
        tmp_stack.append(np.array([[1.0,0,0,translation[0]],
                                  [0,1.0,0,translation[1]],
                                  [0,0,1.0,translation[2]],
                                  [0,0,0,1.0]]))
        #print("translation = {0} ".format(translation), end = '') # imprime no terminal
    
    while(tmp_stack):
        tmp_matrix = np.matmul(tmp_stack.pop(), tmp_matrix)
    op_stack.append(tmp_matrix)

    #print("FINAL transform_matrix")

def _transform():
    """ Função usada para renderizar (na verdade coletar os dados) de Transform. """
    # A função _transform será chamada quando se sair em um nó X3D do tipo Transform do
    # grafo de cena. Não são passados valores, porém quando se sai de um nó transform se
    # deverá recuperar a matriz de transformação dos modelos do mundo da estrutura de
    # pilha implementada.
    while(op_stack): #Faz as operações de transformação na ordem certa
        transform_matrix.matrix = np.matmul(op_stack.pop(),transform_matrix.matrix)
    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    #print("Saindo de Transform")

def triangleStripSet(point, stripCount, color):
    """ Função usada para renderizar TriangleStripSet. """
    # A função triangleStripSet é usada para desenhar tiras de triângulos interconectados,
    # você receberá as coordenadas dos pontos no parâmetro point, esses pontos são uma
    # lista de pontos x, y, e z sempre na ordem. Assim point[0] é o valor da coordenada x
    # do primeiro ponto, point[1] o valor y do primeiro ponto, point[2] o valor z da
    # coordenada z do primeiro ponto. Já point[3] é a coordenada x do segundo ponto e assim
    # por diante. No TriangleStripSet a quantidade de vértices a serem usados é informado
    # em uma lista chamada stripCount (perceba que é uma lista).

    triangles = []
    counter = 0
    for p in range(len(point)):
        if p%3 == 0 and  p<len(point)-8:      
            triangle_result = np.matmul(transform_matrix.matrix,np.array([[point[p],point[p+3],point[p+6]], #multiplica a matriz dos pontos pela matriz de transformação
                                                                        [point[p+1],point[p+4],point[p+7]],
                                                                        [point[p+2],point[p+5],point[p+8]],
                                                                        [1.0,1.0,1.0]]))
            triangle_result = np.matmul(look_at_matrix.matrix,triangle_result) #multiplica o resultado pela matriz look at
            triangle_result = np.matmul(perspective_matrix.matrix,triangle_result)#multiplica o resultado pela matriz perspectiva
            if(triangle_result[3][0]>0): #normalização
                triangle_result[:,0] /= triangle_result[3][0]
            if(triangle_result[3][1]>0):
                triangle_result[:,1] /= triangle_result[3][1]
            if(triangle_result[3][2]>0):
                triangle_result[:,2] /= triangle_result[3][2]

            screen_matrix = np.array([[LARGURA/2.0,0,0,LARGURA/2.0],
                                    [0,-ALTURA/2.0,0,ALTURA/2.0],
                                    [0,0,1.0,0],
                                    [0,0,0,1.0]])
            triangles.append(np.matmul(screen_matrix,triangle_result)) #faz a adequação da matriz normalizada para os pontos da tela
            counter+=1
    for t in triangles:
        triangleSet2D([t[0][0],t[1][0],t[0][1],t[1][1],t[0][2],t[1][2]], color) #faz a rasterizaçao da matriz

    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    # print("TriangleStripSet : pontos = {0} ".format(point), end = '') # imprime no terminal pontos
    # for i, strip in enumerate(stripCount):
    #     print("strip[{0}] = {1} ".format(i, strip), end = '') # imprime no terminal
    # print("")

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

    pr = [] #lista que armazena os pontos me ordem crescente
    for p in range(len(point)):
        if p%3 == 0 and p<len(point)-2:
            pr.append([point[p],point[p+1],point[p+2]])
    
    triangles = []
    iterations = 0
    for t in index:     #Aqui devemos organizar os pontos na ordem do index
        if iterations < len(index)-3:
            triangle_result = np.matmul(transform_matrix.matrix,np.array([[pr[t][0],pr[t+1][0],pr[t+2][0]], #multiplica a matriz dos pontos pela matriz de transformação
                                                                        [pr[t][1],pr[t+1][1],pr[t+2][1]],
                                                                        [pr[t][2],pr[t+1][2],pr[t+2][2]],
                                                                        [1.0,1.0,1.0]]))
            triangle_result = np.matmul(look_at_matrix.matrix,triangle_result) #multiplica o resultado pela matriz look at
            triangle_result = np.matmul(perspective_matrix.matrix,triangle_result)#multiplica o resultado pela matriz perspectiva
            if(triangle_result[3][0]>0): #normalização
                triangle_result[:,0] /= triangle_result[3][0]
            if(triangle_result[3][1]>0):
                triangle_result[:,1] /= triangle_result[3][1]
            if(triangle_result[3][2]>0):
                triangle_result[:,2] /= triangle_result[3][2]

            screen_matrix = np.array([[LARGURA/2.0,0,0,LARGURA/2.0],
                                        [0,-ALTURA/2.0,0,ALTURA/2.0],
                                        [0,0,1.0,0],
                                        [0,0,0,1.0]])
            triangles.append(np.matmul(screen_matrix,triangle_result)) #faz a adequação da matriz normalizada para os pontos da tela
            iterations+=1
    for t in triangles:
        triangleSet2D([t[0][0],t[1][0],t[0][1],t[1][1],t[0][2],t[1][2]], color) #faz a rasterizaçao da matriz
    
    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    #print("IndexedTriangleStripSet : pontos = {0}, index = {1}".format(point, index)) # imprime no terminal pontos

def box(size, color):
    """ Função usada para renderizar Boxes. """
    # A função box é usada para desenhar paralelepípedos na cena. O Box é centrada no
    # (0, 0, 0) no sistema de coordenadas local e alinhado com os eixos de coordenadas
    # locais. O argumento size especifica as extensões da caixa ao longo dos eixos X, Y
    # e Z, respectivamente, e cada valor do tamanho deve ser maior que zero. Para desenha
    # essa caixa você vai provavelmente querer tesselar ela em triângulos, para isso
    # encontre os vértices e defina os triângulos.
    
    points = [[size[0]/2,size[1]/2,size[2]/2],
            [size[0]/2,-size[1]/2,size[2]/2],
            [size[0]/2,-size[1]/2,-size[2]/2],
            [size[0]/2,size[1]/2,-size[2]/2],
            [-size[0]/2,-size[1]/2,-size[2]/2],
            [-size[0]/2,size[1]/2,-size[2]/2],
            [-size[0]/2,size[1]/2,size[2]/2],
            [-size[0]/2,-size[1]/2,size[2]/2]]

    triangles_to_render = [[points[0],points[1],points[2]],
                        [points[0],points[2],points[3]],
                        [points[2],points[3],points[4]],
                        [points[3],points[4],points[5]],
                        [points[4],points[5],points[6]],
                        [points[4],points[6],points[7]],
                        [points[6],points[7],points[1]],
                        [points[6],points[1],points[0]],
                        [points[0],points[6],points[5]],
                        [points[0],points[3],points[5]],
                        [points[1],points[2],points[4]],
                        [points[1],points[7],points[4]]]

    triangles = []
    for t in triangles_to_render: 
        triangle_result = np.matmul(transform_matrix.matrix,np.array([[t[0][0],t[1][0],t[2][0]], #multiplica a matriz dos pontos pela matriz de transformação
                                                                    [t[0][1],t[1][1],t[2][1]],
                                                                    [t[0][2],t[1][2],t[2][2]],
                                                                    [1.0,1.0,1.0]]))
        triangle_result = np.matmul(look_at_matrix.matrix,triangle_result)#multiplica o resultado pela matriz look at
        triangle_result = np.matmul(perspective_matrix.matrix,triangle_result)#multiplica o resultado pela matriz perspectiva
        if(triangle_result[3][0]>0): #normalização
            triangle_result[:,0] /= triangle_result[3][0]
        if(triangle_result[3][1]>0):
            triangle_result[:,1] /= triangle_result[3][1]
        if(triangle_result[3][2]>0):
            triangle_result[:,2] /= triangle_result[3][2]

        screen_matrix = np.array([[LARGURA/2.0,0,0,LARGURA/2.0],
                                    [0,-ALTURA/2.0,0,ALTURA/2.0],
                                    [0,0,1.0,0],
                                    [0,0,0,1.0]])
        triangles.append(np.matmul(screen_matrix,triangle_result))#faz a adequação da matriz normalizada para os pontos da tela
            
    for t in triangles:
        triangleSet2D([t[0][0],t[1][0],t[0][1],t[1][1],t[0][2],t[1][2]], color) #faz a rasterizaçao da matriz
    # O print abaixo é só para vocês verificarem o funcionamento, deve ser removido.
    # print("Box : size = {0}".format(size)) # imprime no terminal pontos


LARGURA = 150
ALTURA = 100
NEAR = 0.5
FAR = 100.0
def indexedFaceSet(coord, coordIndex, colorPerVertex, color, colorIndex, texCoord, texCoordIndex, current_color, current_texture):
    """ Função usada para renderizar IndexedFaceSet. """
    # A função indexedFaceSet é usada para desenhar malhas de triângulos. Ela funciona de
    # forma muito simular a IndexedTriangleStripSet porém com mais recursos.
    # Você receberá as coordenadas dos pontos no parâmetro cord, esses
    # pontos são uma lista de pontos x, y, e z sempre na ordem. Assim point[0] é o valor
    # da coordenada x do primeiro ponto, point[1] o valor y do primeiro ponto, point[2]
    # o valor z da coordenada z do primeiro ponto. Já point[3] é a coordenada x do
    # segundo ponto e assim por diante. No IndexedFaceSet uma lista informando
    # como conectar os vértices é informada em coordIndex, o valor -1 indica que a lista
    # acabou. A ordem de conexão será de 3 em 3 pulando um índice. Por exemplo: o
    # primeiro triângulo será com os vértices 0, 1 e 2, depois serão os vértices 1, 2 e 3,
    # depois 2, 3 e 4, e assim por diante.
    # Adicionalmente essa implementação do IndexedFace suport cores por vértices, assim
    # a se a flag colorPerVertex estiver habilidades, os vértices também possuirão cores
    # que servem para definir a cor interna dos poligonos, para isso faça um cálculo
    # baricêntrico de que cor deverá ter aquela posição. Da mesma forma se pode definir uma
    # textura para o poligono, para isso, use as coordenadas de textura e depois aplique a
    # cor da textura conforme a posição do mapeamento. Dentro da classe GPU já está
    # implementadado um método para a leitura de imagens.

    if texCoord:
        image = gpu.GPU.load_texture(current_texture[0])
        pr = [] #lista que armazena os pontos em ordem crescente
        for p in range(len(coord)):
            if p%3 == 0 and p<len(coord)-2:
                pr.append([coord[p],coord[p+1],coord[p+2]])
        
        iterations = 0
        triangles = []
        for t in range(len(coordIndex)):     #Aqui devemos organizar os pontos na ordem do index
            if iterations < len(coordIndex)-3 and coordIndex[t] != -1 and coordIndex[t+1] != -1 and coordIndex[t+2] != -1:
                triangle_result = np.matmul(transform_matrix.matrix,np.array([[pr[coordIndex[t]][0],pr[coordIndex[t+1]][0],pr[coordIndex[t+2]][0]], #multiplica a matriz dos pontos pela matriz de transformação
                                                                            [pr[coordIndex[t]][1],pr[coordIndex[t+1]][1],pr[coordIndex[t+2]][1]],
                                                                            [pr[coordIndex[t]][2],pr[coordIndex[t+1]][2],pr[coordIndex[t+2]][2]],
                                                                            [1.0,1.0,1.0]]))
                triangle_result = np.matmul(look_at_matrix.matrix,triangle_result) #multiplica o resultado pela matriz look at
                triangle_result = np.matmul(perspective_matrix.matrix,triangle_result)#multiplica o resultado pela matriz perspectiva
                if(triangle_result[3][0]>0): #normalização
                    triangle_result[:,0] /= triangle_result[3][0]
                if(triangle_result[3][1]>0):
                    triangle_result[:,1] /= triangle_result[3][1]
                if(triangle_result[3][2]>0):
                    triangle_result[:,2] /= triangle_result[3][2]

                screen_matrix = np.array([[LARGURA/2.0,0,0,LARGURA/2.0],
                                        [0,-ALTURA/2.0,0,ALTURA/2.0],
                                        [0,0,1.0,0],
                                        [0,0,0,1.0]])
                triangles.append(np.matmul(screen_matrix,triangle_result)) #faz a adequação da matriz normalizada para os pontos da tela
            iterations+=1

        tr = [] #lista que armazena as cores na ordem de entrada
        for c in range(len(texCoord)):
            if c%2 == 0 and c<len(texCoord)-1:
                tr.append([texCoord[c],texCoord[c+1]])
        print(tr)
        texture_iterator = 0
        for t in triangles:
            #triangleSet2D([t[0][0],t[1][0],t[0][1],t[1][1],t[0][2],t[1][2]], color) #faz a rasterizaçao de cada triangulo segundo a média das cores pelo calculo de baricentro
            if texCoordIndex[texture_iterator] != -1 and texCoordIndex[texture_iterator+1] != -1 and texCoordIndex[texture_iterator+2] != -1:
                vertices = [t[0][0],t[1][0],t[0][1],t[1][1],t[0][2],t[1][2]]
                # pontos_da_vez = [tr[texture_iterator], tr[texture_iterator+1], tr[texture_iterator+2]]
                # escala_x = len(image)/(vertices[0]-vertices[1]-vertices[2])
                # escala_y = len(image)/(vertices[1]-vertices[3]-vertices[5])
                # cores_da_vez = [tr[texCoordIndex[texture_iterator]], tr[texCoordIndex[texture_iterator+1]], tr[texCoordIndex[texture_iterator+2]]]
                for l in range(0,LARGURA):
                    for a in range(0,ALTURA):
                        #Multisampling for anti-aliasing (4XAA)
                        multiplier0 = isInside(vertices, [l+0.33,a+0.33])
                        multiplier1 = isInside(vertices, [l+0.33,a+0.66])
                        multiplier2 = isInside(vertices, [l+0.66,a+0.33])
                        multiplier3 = isInside(vertices, [l+0.66,a+0.66])
                        #Final multiplier checks which parts of the pixel are covered by triangle
                        fm = 0.25*multiplier0 + 0.25*multiplier1 + 0.25*multiplier2 + 0.25*multiplier3
                        #calculo da cor naqule pixel

                        color = image[l][a]

                        if fm > 0:
                            gpu.GPU.set_pixel(l, a, 255*fm*color[2], 255*fm*color[1], 255*fm*color[0]) # altera um pixel da imagem
            texture_iterator +=1
            if texture_iterator < len(texCoordIndex)-3:
                while texCoordIndex[texture_iterator] == -1 or texCoordIndex[texture_iterator+1] == -1 or texCoordIndex[texture_iterator+2] == -1:
                    texture_iterator +=1

    elif colorPerVertex:
        pr = [] #lista que armazena os pontos em ordem crescente
        for p in range(len(coord)):
            if p%3 == 0 and p<len(coord)-2:
                pr.append([coord[p],coord[p+1],coord[p+2]])
        
        iterations = 0
        triangles = []
        for t in range(len(coordIndex)):     #Aqui devemos organizar os pontos na ordem do index
            if iterations < len(coordIndex)-3 and coordIndex[t] != -1 and coordIndex[t+1] != -1 and coordIndex[t+2] != -1:
                triangle_result = np.matmul(transform_matrix.matrix,np.array([[pr[coordIndex[t]][0],pr[coordIndex[t+1]][0],pr[coordIndex[t+2]][0]], #multiplica a matriz dos pontos pela matriz de transformação
                                                                            [pr[coordIndex[t]][1],pr[coordIndex[t+1]][1],pr[coordIndex[t+2]][1]],
                                                                            [pr[coordIndex[t]][2],pr[coordIndex[t+1]][2],pr[coordIndex[t+2]][2]],
                                                                            [1.0,1.0,1.0]]))
                triangle_result = np.matmul(look_at_matrix.matrix,triangle_result) #multiplica o resultado pela matriz look at
                triangle_result = np.matmul(perspective_matrix.matrix,triangle_result)#multiplica o resultado pela matriz perspectiva
                if(triangle_result[3][0]>0): #normalização
                    triangle_result[:,0] /= triangle_result[3][0]
                if(triangle_result[3][1]>0):
                    triangle_result[:,1] /= triangle_result[3][1]
                if(triangle_result[3][2]>0):
                    triangle_result[:,2] /= triangle_result[3][2]

                screen_matrix = np.array([[LARGURA/2.0,0,0,LARGURA/2.0],
                                        [0,-ALTURA/2.0,0,ALTURA/2.0],
                                        [0,0,1.0,0],
                                        [0,0,0,1.0]])
                triangles.append(np.matmul(screen_matrix,triangle_result)) #faz a adequação da matriz normalizada para os pontos da tela
            iterations+=1

        cr = [] #lista que armazena as cores na ordem de entrada
        for c in range(len(color)):
            if c%3 == 0 and c<len(color)-2:
                cr.append([color[c],color[c+1],color[c+2]])
        color_iterator = 0
        for t in triangles:
            #triangleSet2D([t[0][0],t[1][0],t[0][1],t[1][1],t[0][2],t[1][2]], color) #faz a rasterizaçao de cada triangulo segundo a média das cores pelo calculo de baricentro
            if colorIndex[color_iterator] != -1 and colorIndex[color_iterator+1] != -1 and colorIndex[color_iterator+2] != -1:
                vertices = [t[0][0],t[1][0],t[0][1],t[1][1],t[0][2],t[1][2]]
                cores_da_vez = [cr[colorIndex[color_iterator]], cr[colorIndex[color_iterator+1]], cr[colorIndex[color_iterator+2]]]
                for l in range(0,LARGURA):
                    for a in range(0,ALTURA):
                        #Multisampling for anti-aliasing (4XAA)
                        multiplier0 = isInside(vertices, [l+0.33,a+0.33])
                        multiplier1 = isInside(vertices, [l+0.33,a+0.66])
                        multiplier2 = isInside(vertices, [l+0.66,a+0.33])
                        multiplier3 = isInside(vertices, [l+0.66,a+0.66])
                        #Final multiplier checks which parts of the pixel are covered by triangle
                        fm = 0.25*multiplier0 + 0.25*multiplier1 + 0.25*multiplier2 + 0.25*multiplier3
                        #calculo do alpha
                        alpha = (-(l-vertices[2])*(vertices[5]-vertices[3])+(a-vertices[3])*(vertices[4]-vertices[2]))/(-(vertices[0]-vertices[2])*(vertices[5]-vertices[3])+(vertices[1]-vertices[3])*(vertices[4]-vertices[2]))
                        beta = (-(l-vertices[4])*(vertices[1]-vertices[5])+(a-vertices[5])*(vertices[0]-vertices[4]))/(-(vertices[2]-vertices[4])*(vertices[1]-vertices[5])+(vertices[3]-vertices[5])*(vertices[0]-vertices[4]))
                        gamma = 1 - alpha - beta
                        if fm > 0:
                            gpu.GPU.set_pixel(l, a, 255*fm*(cores_da_vez[0][0]*alpha+cores_da_vez[1][0]*beta+cores_da_vez[2][0]*gamma), 255*fm*(cores_da_vez[0][1]*alpha+cores_da_vez[1][1]*beta+cores_da_vez[2][1]*gamma), 255*fm*(cores_da_vez[0][2]*alpha+cores_da_vez[1][2]*beta+cores_da_vez[2][2]*gamma)) # altera um pixel da imagem
            color_iterator +=1
            if color_iterator < len(colorIndex)-3:
                while colorIndex[color_iterator] == -1 or colorIndex[color_iterator+1] == -1 or colorIndex[color_iterator+2] == -1:
                    color_iterator +=1
    else:
        pr = [] #lista que armazena os pontos em ordem crescente
        for p in range(len(coord)):
            if p%3 == 0 and p<len(coord)-2:
                pr.append([coord[p],coord[p+1],coord[p+2]])
        
        iterations = 0
        triangles = []
        for t in range(len(coordIndex)):     #Aqui devemos organizar os pontos na ordem do index
            if iterations < len(coordIndex)-3 and coordIndex[t] != -1 and coordIndex[t+1] != -1 and coordIndex[t+2] != -1:
                triangle_result = np.matmul(transform_matrix.matrix,np.array([[pr[coordIndex[t]][0],pr[coordIndex[t+1]][0],pr[coordIndex[t+2]][0]], #multiplica a matriz dos pontos pela matriz de transformação
                                                                            [pr[coordIndex[t]][1],pr[coordIndex[t+1]][1],pr[coordIndex[t+2]][1]],
                                                                            [pr[coordIndex[t]][2],pr[coordIndex[t+1]][2],pr[coordIndex[t+2]][2]],
                                                                            [1.0,1.0,1.0]]))
                triangle_result = np.matmul(look_at_matrix.matrix,triangle_result) #multiplica o resultado pela matriz look at
                triangle_result = np.matmul(perspective_matrix.matrix,triangle_result)#multiplica o resultado pela matriz perspectiva
                if(triangle_result[3][0]>0): #normalização
                    triangle_result[:,0] /= triangle_result[3][0]
                if(triangle_result[3][1]>0):
                    triangle_result[:,1] /= triangle_result[3][1]
                if(triangle_result[3][2]>0):
                    triangle_result[:,2] /= triangle_result[3][2]

                screen_matrix = np.array([[LARGURA/2.0,0,0,LARGURA/2.0],
                                        [0,-ALTURA/2.0,0,ALTURA/2.0],
                                        [0,0,1.0,0],
                                        [0,0,0,1.0]])
                triangles.append(np.matmul(screen_matrix,triangle_result)) #faz a adequação da matriz normalizada para os pontos da tela
            iterations+=1

        #A variavel color está chegando como None, então é preciso redefinir-la para a cor desejada
        color=[1,1,1]
        for t in triangles:
            triangleSet2D([t[0][0],t[1][0],t[0][1],t[1][1],t[0][2],t[1][2]], color) #faz a rasterizaçao de cada triangulo segundo a média das cores pelo calculo de baricentro
            
    # print("IndexedFaceSet : ")
    # if coord:
    #     print("\tpontos(x, y, z) = {0}, coordIndex = {1}".format(coord, coordIndex)) # imprime no terminal
    # if colorPerVertex:
    #     print("\tcores(r, g, b) = {0}, colorIndex = {1}".format(color, colorIndex)) # imprime no terminal
    # if texCoord:
    #     print("\tpontos(u, v) = {0}, texCoordIndex = {1}".format(texCoord, texCoordIndex)) # imprime no terminal
    # if(current_texture):
    #     image = gpu.GPU.load_texture(current_texture[0])
    #     print("\t Matriz com image = {0}".format(image))

if __name__ == '__main__':

    op_stack = []
    transform_matrix = Matrix()
    look_at_matrix = Matrix()
    perspective_matrix = Matrix()

    # Valores padrão da aplicação
    width = LARGURA
    height = ALTURA
    x3d_file = "exemplo9.x3d"
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
    x3d.X3D.render["IndexedFaceSet"] = indexedFaceSet

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
