import math
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

class Position:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __eq__(self, other):
        return (self.x == other.x) and (self.y == other.y) and (self.z == other.z)

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)

    def __iadd__(self, other):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)

    def __isub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __mul__(self, scalar):
        return Position(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar):
        return self.__mul__(scalar)

    def __imul__(self, scalar):
        self.x *= scalar
        self.y *= scalar
        self.z *= scalar
        return self

    def __truediv__(self, scalar):
        return Position(self.x / scalar, self.y / scalar, self.z / scalar)

    def __idiv__(self, scalar):
        self.x /= scalar
        self.y /= scalar
        self.z /= scalar
        return self

    def set(self, strXYZ=None, tupXYZ=None):
        if strXYZ:
            parts = strXYZ.replace('(', '').replace(')', '').split(',')
            self.x, self.y, self.z = map(float, parts)
        elif tupXYZ:
            self.x, self.y, self.z = tupXYZ

    def get_tuple(self):
        return (self.x, self.y, self.z)

    def get_str(self, n_places=3):
        return "{}, {}, {}".format(round(self.x, n_places), round(self.y, n_places), round(self.z, n_places))

    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def normalize(self):
        mag = self.magnitude()
        if mag > 0:
            self.x /= mag
            self.y /= mag
            self.z /= mag

    def get_angle_rad(self):
        if self.magnitude() == 0:
            return 0
        return math.atan2(self.y, self.x)

    def get_angle_deg(self):
        return math.degrees(self.get_angle_rad())
class Material():
    def __init__(self, uts=None, ys=None, modulus=None, staticFactor=None):
        self.uts = uts
        self.ys = ys
        self.E=modulus
        self.staticFactor=staticFactor

class Node():
    def __init__(self, name=None, position=None):
        self.name = name
        self.position = position if position is not None else Position()

    def __eq__(self, other):
        """
        This overloads the == operator such that I can compare two nodes to see if they are the same node.  This is
        useful when reading in nodes to make sure I don't get duplicate nodes
        """
        if self.name != other.name:
            return False
        if self.position != other.position:
            return False
        return True

class Link():
    def __init__(self,name="", node1="1", node2="2", length=None, angleRad=None):
        """
        Basic definition of a link contains a name and names of node1 and node2
        """
        self.name=""
        self.node1_Name=node1
        self.node2_Name=node2
        self.length=None
        self.angleRad=None

    def __eq__(self, other):
        """
        This overloads the == operator for comparing equivalence of two links.
        """
        if self.node1_Name != other.node1_Name: return False
        if self.node2_Name != other.node2_Name: return False
        if self.length != other.length: return False
        if self.angleRad != other.angleRad: return False
        return True

    def set(self, node1=None, node2=None, length=None, angleRad=None):
        self.node1_Name=node1
        self.node2_Name=node2
        self.length=length
        self.angleRad=angleRad

class TrussModel():
    def __init__(self):
        self.title=None
        self.links=[]
        self.nodes=[]
        self.material=Material()

    def getNode(self, name):
       for n in self.nodes:
           if n.name == name:
               return n

class TrussController():
    def __init__(self):
        self.truss=TrussModel()
        self.view=TrussView()

    def ImportFromFile(self, data):
        """
        Data is the list of strings read from the data file.
        We need to parse this file and build the lists of nodes and links that make up the truss.
        Also, we need to parse the lines that give the truss title, material (and strength values).

        Reading Nodes:
        I create a new node object and the set its name and position.x and position.y values.  Next, I check to see
        if the list of nodes in the truss model has this node with self.hasNode(n.name).  If the trussModel does not
        contain the node, I append it to the list of nodes

        Reading Links:
        The links should come after the nodes.  Each link has a name and two node names.  See method addLink
        """
        for line in data:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip comments and empty lines

            # Debug output to understand the exact content of 'parts' after splitting
            print("Original line:", line)

            try:
                # Using split with a comma and stripping each part to handle spaces
                parts = [part.strip() for part in line.split(',')]
                print("Parsed parts:", parts)  # Debug output

                if len(parts) < 2:
                    print("Skipped line: not enough parts")
                    continue

                keyword = parts[0].lower()
                if 'node' in keyword and len(parts) >= 4:
                    self.process_node(parts)
                elif 'link' in keyword and len(parts) >= 4:
                    self.process_link(parts)
                elif 'title' in keyword:
                    self.truss.title = parts[1].strip().strip("'")
                elif 'material' in keyword and len(parts) >= 4:
                    self.process_material(parts)
                elif 'static_factor' in keyword:
                    self.truss.material.staticFactor = float(parts[1])
            except Exception as e:
                print(f"Error processing line: {line}. Error: {e}")
                continue  # Skip lines that cause errors

        self.calcLinkVals()
        self.displayReport()
        self.drawTruss()

    def process_node(self, parts):
        """
        Process node data from input parts.
        """
        try:
            name = parts[1]
            x, y = float(parts[2]), float(parts[3])
            if not self.hasNode(name):
                node_position = Position(x=x, y=y)
                new_node = Node(name=name, position=node_position)
                self.addNode(new_node)
            else:
                print(f"Node {name} already exists.")
        except ValueError as e:
            print(f"Error processing node data {parts}: {e}")
        except IndexError as e:
            print(f"Error processing line, missing data {parts}: {e}")

    def process_link(self, parts):
        """
        Process link data from input parts.
        """
        name, node1, node2 = parts[1], parts[2], parts[3]
        if not self.hasNode(node1) or not self.hasNode(node2):
            print(f"Skipping link {name}: Node {node1} or {node2} not found.")
            return
        self.addLink(Link(name, node1, node2))

    def process_material(self, parts):
        """
        Process material data from input parts.
        """
        try:
            uts, ys, modulus = float(parts[1]), float(parts[2]), float(parts[3])
            self.truss.material = Material(uts, ys, modulus)
        except ValueError as e:
            print(f"Error processing material data: {e}")

    def hasNode(self, name):
        for n in self.truss.nodes:
            if n.name==name:
                return True
        return False

    def addNode(self, node):
        self.truss.nodes.append(node)

    def getNode(self, name):
        for n in self.truss.nodes:
            if n.name == name:
                return n

    def addLink(self, link):
        self.truss.links.append(link)

    def calcLinkVals(self):
        print("Starting calcLinkVals")
        try:
            for l in self.truss.links:
                print("Processing link:", l.name)
                n1 = self.truss.getNode(l.node1_Name)
                n2 = self.truss.getNode(l.node2_Name)
                if n1 is None or n2 is None:
                    print("Error: One of the nodes in the link is None")
                    continue
                # Assuming Position has x, y attributes
                dx = n2.position.x - n1.position.x
                dy = n2.position.y - n1.position.y
                l.length = math.sqrt(dx ** 2 + dy ** 2)
                if dx == 0 and dy == 0:
                    l.angleRad = 0
                else:
                    l.angleRad = math.atan2(dy, dx)
                print(f"Link {l.name}: length = {l.length}, angle = {l.angleRad}")
        except Exception as e:
            print("Exception in calcLinkVals:", e)
        print("Finished calcLinkVals")

    def setDisplayWidgets(self, args):
        self.view.setDisplayWidgets(args)

    def displayReport(self):
        self.view.displayReport(truss=self.truss)

    def drawTruss(self):
        self.view.buildScene(truss=self.truss)


class RigidLink(qtw.QGraphicsItem):
    def __init__(self, stX, stY, enX, enY, radius=10, parent = None, pen=None, brush=None):
        """
        This is a custom class for drawing a rigid link.  The paint function executes everytime the scene
        which holds the link is updated.  The steps to making the link are:
        1. Specify the start and end x,y coordinates of the link
        2. Specify the radius (i.e., the width of the link)
        3. Compute the length of the link
        3. Compute the angle of the link relative to the x-axis
        4. Compute the angle normal the angle of the length by adding pi/2
        5. Compute the rectangle that will contain the link (i.e., its bounding box)
        These steps are executed each time the paint function is invoked
        :param stX:
        :param stY:
        :param enX:
        :param enY:
        :param radius:
        :param parent:
        :param pen:
        :param brush:
        """
        super().__init__(parent)
        #step 1
        self.startX = stX
        self.startY = stY
        self.endX = enX
        self.endY = enY
        #step 2
        self.radius = radius
        #step 3
        self.length=self.linkLength()
        #step 4
        self.angle = self.linkAngle()
        #step 5
        self.normAngle = self.angle+math.pi/2
        #step 6
        self.width=self.endX-self.startX+2*self.radius
        self.height=self.endY-self.startY+2*self.radius
        self.rect=qtc.QRectF(self.startX, self.startY, self.width, self.height)

        self.pen=pen
        self.brush=brush

    def boundingRect(self):
        return self.rect

    def linkLength(self):
        self.length = math.sqrt(math.pow(self.startX - self.endX, 2) + math.pow(self.startY - self.endY, 2))
        return self.length

    def linkAngle(self):
        self.angle= math.acos((self.endX-self.startX)/self.linkLength())
        self.angle *= -1 if (self.endY>self.startY) else 1
        return self.angle

    def paint(self, painter, option, widget=None):
        """
        This function creates a path painter the paints a semicircle around the start point (ccw), a straight line
        offset from the main axis of the link, a semicircle around the end point (ccw), and a straight line offset from
        the main axis.  It then assigns a pen and brush.  Finally, it draws a circle at the start and end points to
        indicate the pivot points.
        :param painter:
        :param option:
        :param widget:
        :return:
        """
        path = qtg.QPainterPath()
        len = self.linkLength()
        angLink = self.linkAngle()*180/math.pi
        perpAng = angLink+90
        xOffset = self.radius*math.cos(perpAng*math.pi/180)
        yOffset = -self.radius*math.sin(perpAng*math.pi/180)
        rectStart = qtc.QRectF(self.startX-self.radius, self.startY-self.radius, 2*self.radius, 2*self.radius)
        rectEnd = qtc.QRectF(self.endX-self.radius, self.endY-self.radius, 2*self.radius, 2*self.radius)
        centerLinePen= qtg.QPen()
        centerLinePen.setStyle(qtc.Qt.DashDotLine)
        r,g,b,a=self.pen.color().getRgb()
        centerLinePen.setColor(qtg.QColor(r,g,b,128))
        centerLinePen.setWidth(1)
        p1=qtc.QPointF(self.startX, self.startY)
        p2=qtc.QPointF(self.endX, self.endY)
        painter.setPen(centerLinePen)
        painter.drawLine(p1,p2)
        path.arcMoveTo(rectStart, perpAng)
        path.arcTo(rectStart, perpAng, 180)
        path.lineTo(self.endX-xOffset, self.endY-yOffset)
        path.arcMoveTo(rectEnd, perpAng+180)
        path.arcTo(rectEnd, perpAng+180, 180)
        path.lineTo(self.startX+xOffset, self.startY+yOffset)
        if self.pen is not None:
            painter.setPen(self.pen)  # Red color pen
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawPath(path)
        pivotStart=qtc.QRectF(self.startX-self.radius/6, self.startY-self.radius/6, self.radius/3, self.radius/3)
        pivotEnd=qtc.QRectF(self.endX-self.radius/6, self.endY-self.radius/6, self.radius/3, self.radius/3)
        painter.drawEllipse(pivotStart)
        painter.drawEllipse(pivotEnd)

class RigidPivotPoint(qtw.QGraphicsItem):
    def __init__(self, ptX, ptY, pivotHeight, pivotWidth, parent=None, pen=None, brush=None, rotation=0):
        super().__init__(parent)
        self.x = ptX
        self.y = ptY
        self.pen = pen
        self.brush = brush
        self.height = pivotHeight
        self.width = pivotWidth
        self.radius = min(self.height, self.width) / 4
        self.rect = qtc.QRectF(self.x - self.width / 2, self.y - self.radius, self.width, self.height + self.radius)
        self.rotationAngle = rotation

    def boundingRect(self):
        return self.rect
    def rotate(self, angle):
        self.rotationAngle=angle


    def paint(self, painter, option, widget=None):
        path = qtg.QPainterPath()
        radius = min(self.height,self.width)/2
        rect = qtc.QRectF(self.x-self.width/2, self.y-radius, self.width,self.height+radius)
        H=math.sqrt(math.pow(self.width/2,2)+math.pow(self.height,2))
        phi=math.asin(radius/H)
        theta=math.asin(self.height/H)
        ang=math.pi-phi-theta
        l=H*math.cos(phi)
        x1=self.x+self.width/2
        y1=self.y+self.height
        path.moveTo(x1,y1)
        x2=l*math.cos(ang)
        y2=l*math.sin(ang)
        path.lineTo(x1+x2, y1-y2)
        pivotRect=qtc.QRectF(self.x-radius, self.y-radius, 2*radius, 2*radius)
        stAng=math.pi/2-phi-theta
        spanAng=math.pi-2*stAng
        path.arcTo(pivotRect,stAng*180/math.pi, spanAng*180/math.pi)
        x4=self.x-self.width/2
        y4=self.y+self.height
        path.lineTo(x4,y4)
        #path.arcTo(pivotRect,ang*180/math.pi, 90)
        if self.pen is not None:
            painter.setPen(self.pen)  # Red color pen
        if self.brush is not None:
            painter.setBrush(self.brush)
        painter.drawPath(path)

        pivotPtRect=qtc.QRectF(self.x-radius/4, self.y-radius/4, radius/2,radius/2)
        painter.drawEllipse(pivotPtRect)
        x5=self.x-self.width
        x6=self.x+self.width
        painter.drawLine(x5,y4,x6,y4)
        penOutline = qtg.QPen(qtc.Qt.NoPen)
        hatchbrush = qtg.QBrush(qtc.Qt.BDiagPattern)
        painter.setPen(penOutline)
        painter.setBrush(hatchbrush)
        support = qtc.QRectF(x5,y4,self.width*2, self.height)
        painter.drawRect(support)
        self.setRotation(self.rotationAngle)

class ArcItem(qtw.QGraphicsItem):
    def __init__(self, rect, start_angle, span_angle, parent=None, pen=None):
        super().__init__(parent)
        self.rect = rect
        self.start_angle = start_angle
        self.span_angle = span_angle
        self.pen = pen if pen is not None else qtg.QPen()

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        path = qtg.QPainterPath()
        path.arcMoveTo(self.rect,self.start_angle)
        path.arcTo(self.rect, self.start_angle,self.span_angle)
        painter.setPen(self.pen)  # Red color pen
        painter.drawPath(path)


class TrussView():
    def __init__(self):
        #setup widgets for display.  redefine these when you have a gui to work with using setDisplayWidgets
        self.scene=qtw.QGraphicsScene()
        self.le_LongLinkName=qtw.QLineEdit()
        self.le_LongLinkNode1=qtw.QLineEdit()
        self.le_LongLinkNode2=qtw.QLineEdit()
        self.le_LongLinkLength=qtw.QLineEdit()
        self.te_Report=qtw.QTextEdit()
        self.gv=qtw.QGraphicsView()

        #region setup pens and brushes and scene
        #make the pens first
        #a thick darkGray pen
        self.penLink = qtg.QPen(qtc.Qt.darkGray)
        self.penLink.setWidth(4)
        #a medium darkBlue pen
        self.penNode = qtg.QPen(qtc.Qt.darkBlue)
        self.penNode.setStyle(qtc.Qt.SolidLine)
        self.penNode.setWidth(1)
        #a pen for the grid lines
        self.penGridLines = qtg.QPen()
        self.penGridLines.setWidth(1)
        # I wanted to make the grid lines more subtle, so set alpha=25
        self.penGridLines.setColor(qtg.QColor.fromHsv(197, 144, 228, alpha=50))
        #now make some brushes
        #build a brush for filling with solid red
        self.brushFill = qtg.QBrush(qtc.Qt.darkRed)
        #a brush that makes a hatch pattern
        self.brushNode = qtg.QBrush(qtg.QColor.fromCmyk(0,0,255,0,alpha=100))
        #a brush for the background of my grid
        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, alpha=128))
        #endregion

    def setDisplayWidgets(self, args):
        self.te_Report = args[0]
        self.le_LongLinkName = args[1]
        self.le_LongLinkNode1 = args[2]
        self.le_LongLinkNode2 = args[3]
        self.le_LongLinkLength = args[4]
        self.gv = args[5]
        self.gv.setScene(self.scene)

    def displayReport(self, truss=None):
        st = '\tTruss Design Report\n'
        st += 'Title:  {}\n'.format(truss.title)
        st += 'Static Factor of Safety:  {:0.2f}\n'.format(truss.material.staticFactor)
        st += 'Ultimate Strength:  {:0.2f}\n'.format(truss.material.uts)
        st += 'Yield Strength:  {:0.2f}\n'.format(truss.material.ys)
        st += 'Modulus of Elasticity:  {:0.2f}\n'.format(truss.material.E)
        st += '_____________Link Summary________________\n'
        st += 'Link\t(1)\t(2)\tLength\tAngle\n'
        longest = None
        for l in truss.links:
            if longest is None or l.length > longest.length:
                longest = l
            st += '{}\t{}\t{}\t{:0.2f}\t{:0.2f}\n'.format(l.name, l.node1_Name, l.node2_Name, l.length, l.angleRad)
        self.te_Report.setText(st)
        self.le_LongLinkName.setText(longest.name)
        self.le_LongLinkLength.setText("{:0.2f}".format(longest.length))
        self.le_LongLinkNode1.setText(longest.node1_Name)
        self.le_LongLinkNode2.setText(longest.node2_Name)

    def buildScene(self, truss):
        # Constructs the scene with a grid and draws nodes and links
        if not truss.nodes:
            print("No nodes available to build the scene.")
            return

        self.scene.clear()
        self.drawAGrid()
        self.drawLinks(truss)
        self.drawNodes(truss)

    def drawAGrid(self, DeltaX=10, DeltaY=10, Height=320, Width=320, CenterX=120, CenterY=60):
        # Draws a reference grid in the scene
        startX = CenterX - Width // 2
        endX = CenterX + Width // 2
        startY = CenterY - Height // 2
        endY = CenterY + Height // 2
        for x in range(startX, endX + 1, DeltaX):
            self.scene.addLine(x, startY, x, endY, self.penGridLines)
        for y in range(startY, endY + 1, DeltaY):
            self.scene.addLine(startX, y, endX, y, self.penGridLines)

    def drawLinks(self, truss):
        # Draws all links between nodes in the truss
        for link in truss.links:
            node1 = truss.getNode(link.node1_Name)
            node2 = truss.getNode(link.node2_Name)
            if node1 and node2:
                self.scene.addLine(node1.position.x, node1.position.y, node2.position.x, node2.position.y, self.penLink)

    def drawNodes(self, truss):
        # Draws all nodes in the truss
        for node in truss.nodes:
            self.scene.addEllipse(node.position.x - 5, node.position.y - 5, 10, 10, self.penNode, self.brushNode)

    def drawALabel(self, x, y, str='', pen=None, brush=None, tip=None):
        # Draws a label at the specified position
        text_item = self.scene.addText(str, qtg.QFont("Arial", 12))
        text_item.setPos(x, y)
        text_item.setDefaultTextColor(pen.color() if pen else qtg.QColor('black'))
        if tip:
            text_item.setToolTip(tip)

    def drawACircle(self, centerX, centerY, Radius, angle=0, brush=None, pen=None, name=None, tooltip=None):
        # Set default pen and brush if not provided
        if not pen:
            pen = self.penNode  # Default to node pen if no pen provided
        if not brush:
            brush = self.brushNode  # Default to node brush if no brush provided

        # Create the ellipse item with the given parameters
        ellipse = self.scene.addEllipse(centerX - Radius, centerY - Radius, 2 * Radius, 2 * Radius, pen, brush)
        if tooltip:
            ellipse.setToolTip(tooltip)
        if name:
            ellipse.setData(0, name)  # Use data slot 0 to store the name if provided

        return ellipse


