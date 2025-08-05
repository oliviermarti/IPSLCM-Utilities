'''
Colors recommanded by IPCC

IPCC Visual Style Guide for Authors
IPCC WGI Technical Support Unit

https://www.ipcc.ch/site/assets/uploads/2019/04/IPCC-visual-style-guide.pdf

Includes ColorShading, ColorLine, RCPColorLine, RCPColorShading

'''
import types

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
# plt.rcParams ['axes.prop_cycle'] = plt.cycler ('color', IPCC.ColorLineHexa )

def color2hex ( r:int, g:int, b:int ) -> str :
    return "#{:02X}{:02X}{:02X}".format ( int(r*255), int(g*255), int(b*255) )

Color = types.SimpleNamespace ()
Style = types.SimpleNamespace ()

# Shading
Color.Shading = [ 
    np.array ([128, 128, 128])/255,
    np.array ([ 91, 174, 178])/255,
    np.array ([204, 174, 113])/255,
    np.array ([191, 191, 191])/255,
    np.array ([ 67, 147, 195])/255,
    np.array ([223, 237, 195])/255]

Color.ShadingHexa = list ( map ( lambda x: color2hex (*x), Color.Shading ) )

# Lines
Color.Line = [
    np.array ([  0,   0,   0])/255,
    np.array ([112, 160, 205])/255,
    np.array ([196, 121,   0])/255,
    np.array ([178, 178, 178])/255,
    np.array ([  0,  52, 102])/255,
    np.array ([  0,  79,   0])/255, ]
Style.Line = ['-',]*len(Color.Line)
Style.Line.extend( ['-.']*len(Color.Line))

Color.Line.extend(Color.Line)


Color.LineHexa = list ( map ( lambda x: color2hex (*x), Color.Line ) )

# Markers
Marker = [
    {"marker":"p", "fillstyle":"full"},
    {"marker":"s", "fillstyle":"full"},
    {"marker":"^", "fillstyle":"full"},
    {"marker":"v", "fillstyle":"full"},
    {"marker":"<", "fillstyle":"full"},
    {"marker":">", "fillstyle":"full"},
    {"marker":"p", "fillstyle":"none"},
    {"marker":"s", "fillstyle":"none"},
    {"marker":"^", "fillstyle":"none"},
    {"marker":"v", "fillstyle":"none"},
    {"marker":"<", "fillstyle":"none"},
    {"marker":">", "fillstyle":"none"}, ]


# RCPs
RCP = types.SimpleNamespace ()

## Lines
RCP.ColorLine = {
    'RCP8.5':np.array([153,   0,   2])/255,
    'RCP6.0':np.array([196, 121,   0])/255,
    'RCP4.5':np.array([112, 160, 205])/255,
    'RCP2.6':np.array([  0,  52, 102])/255 }

RCP.ColorLineHexa = dict (zip (RCP.ColorLine.keys(), list (map(lambda x: color2hex (*x), RCP.ColorLine.values()))))

## Shading
RCP.ColorShading = {
    'RCP8.5':np.array([252, 209, 197])/255,
    'RCP6.0':np.array([204, 174, 113])/255,
    'RCP4.5':np.array([146, 197, 222])/255,
    'RCP2.6':np.array([ 67, 147, 195])/255 }
    
RCP.ColorShadingHexa = dict (zip (RCP.ColorShading.keys(), list(map(lambda x: color2hex (*x), RCP.ColorShading.values()))))

def c2c (tab) :
    ztab = tab
    if not isinstance (ztab, np.ndarray):
        ztab = np.array (ztab, dtype='float')
    if len (ztab.shape) == 1 :
        ztab = np.reshape (ztab, (ztab.shape[0]//3, 3))
    return ztab
        
def create_colormap (colors, position=None, bit=True, reverse=False, name='custom_colormap', liste=False, continuous=False):
    """
    returns a linear custom colormap

    From https://github.com/CSlocumWX/custom_colormap

    Parameters
    ----------
    colors : array-like
        contain RGB values. The RGB values may either be in 8-bit [0 to 255]
        or arithmetic [0 to 1] (default).
        Arrange your tuples so that the first color is the lowest value for the
        colorbar and the last is the highest.
    position : array like
        contains values from 0 to 1 to dictate the location of each color.
    bit : Boolean
        8-bit [0 to 255] (in which bit must be set to
        True when called) or arithmetic [0 to 1] (default)
    reverse : Boolean
        If you want to flip the scheme
    name : string
        name of the scheme if you plan to save it

    Returns
    -------
    cmap : matplotlib.colors.LinearSegmentedColormap
        cmap with equally spaced colors
    """
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap
    if not isinstance (colors, np.ndarray):
        colors = np.array (colors, dtype='float')
    if liste or len (colors.shape) == 1 :
        colors = np.reshape (colors, (colors.shape[0]//3, 3) )
    if reverse:
        colors = colors[::-1]
    if position is not None and not isinstance (position, np.ndarray):
        position = np.array (position)
    elif position is None:
        position = np.linspace (0, 1, colors.shape[0])
    else:
        if position.size != colors.shape[0]:
            raise ValueError("position length must be the same as colors")
        elif not np.isclose(position[0], 0) and not np.isclose(position[-1], 1):
            raise ValueError("position must start with 0 and end with 1")
    if bit:
        colors[:] = [tuple(map(lambda x: x / 255., color)) for color in colors]
    cdict = {'red':[], 'green':[], 'blue':[]}
    if continuous : 
        for pos, color in zip (position, colors):
            cdict ['red']  .append((pos, color[0], color[0]))
            cdict ['green'].append((pos, color[1], color[1]))
            cdict ['blue'] .append((pos, color[2], color[2]))
        return LinearSegmentedColormap (name, cdict, 256)
    else :
        return ListedColormap (colors)
    #

def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    '''
    https://stackoverflow.com/a/18926541
    '''
    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)
    new_cmap = mpl.colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap
    

cmap = types.SimpleNamespace ()

# Shading
cmap.colors_shading = [[128, 128, 128], [91, 174, 178], [204, 174, 113], [191, 191, 191], [67, 147, 195], [223, 237, 195]]
cmap.shading   =  create_colormap (cmap.colors_shading, reverse=False, name='shading'  )
cmap.shading_r =  create_colormap (cmap.colors_shading, reverse=False, name='shading_r'  )

# Qualitative
cmap.colors_qualitative = [[0, 0, 0], [112, 160, 205], [196, 121, 0], [178, 178, 178], [0, 52, 102], [0, 79, 0]]
cmap.qualitative_2   = create_colormap (cmap.colors_qualitative[0:2], reverse=False, name='qualitative_2'  )
cmap.qualitative_2_r = create_colormap (cmap.colors_qualitative[0:2], reverse=True , name='qualitative_2_r')

cmap.qualitative_3   = create_colormap (cmap.colors_qualitative[0:3], reverse=False, name='qualitative_3'  )
cmap.qualitative_3_r = create_colormap (cmap.colors_qualitative[0:3], reverse=True , name='qualitative_3_r')

cmap.qualitative_4   = create_colormap (cmap.colors_qualitative[0:4], reverse=False, name='qualitative_4'  )
cmap.qualitative_4_r = create_colormap (cmap.colors_qualitative[0:4], reverse=True , name='qualitative_4_r')

cmap.qualitative_5   = create_colormap (cmap.colors_qualitative[0:5], reverse=False, name='qualitative_5'  )
cmap.qualitative_5_r = create_colormap (cmap.colors_qualitative[0:5], reverse=True , name='qualitative_5_r')

cmap.qualitative_6   = create_colormap (cmap.colors_qualitative[0:6], reverse=False, name='qualitative_6'  )
cmap.qualitative_6_r = create_colormap (cmap.colors_qualitative[0:6], reverse=True , name='qualitative_6_r')

cmap.qualitative     = create_colormap (cmap.colors_qualitative, reverse=False, name='qualitative'  )
cmap.qualitative_r   = create_colormap (cmap.colors_qualitative, reverse=True , name='qualitative_r')

# Precip 5 cmap.colors
cmap.colors_precip_5 = [[166, 97, 26], [223, 194, 125], [245, 245, 245], [128, 205, 193], [1, 133, 113]]
cmap.precip_5   = create_colormap (cmap.colors_precip_5, reverse=False,  name='precip_5'  )
cmap.precip_5_r = create_colormap (cmap.colors_precip_5, reverse=True ,  name='precip_5_r')

# Precip 6 colors
cmap.colors_precip_6 = [[140, 81, 10], [216, 179, 101] ,[246, 232, 195], [199, 234, 229], [90, 180, 172], [1, 102, 94]]
cmap.precip_6   = create_colormap (cmap.colors_precip_6, reverse=False, name='precip_6'  )
cmap.precip_6_r = create_colormap (cmap.colors_precip_6, reverse=True , name='precip_6_r')

# Precip 7 colors
cmap.colors_precip_7 = [[140,  81,  10], [216, 179, 101], [246, 232, 195],
                        [245, 245, 245], [199, 234, 229], [ 90, 180, 172], [1, 102, 94]]
cmap.precip_7   = create_colormap (cmap.colors_precip_7, reverse=False, name='precip_7'  )
cmap.precip_7_r = create_colormap (cmap.colors_precip_7, reverse=True , name='precip_7_r')

# Precip 8 colors
cmap.colors_precip_8 = [[140,  81,  10], [191, 129, 45], [223, 194, 125], [246, 232, 195],
                        [199, 234, 229], [128, 205, 193], [53, 151, 143], [1, 102, 94]]
cmap.precip_8   = create_colormap (cmap.colors_precip_8, reverse=False, name='precip_8'  )
cmap.precip_8_r = create_colormap (cmap.colors_precip_8, reverse=True , name='precip_8_r')

# Precip 9 colors
cmap.colors_precip_9 = [[140,  81,  10], [191, 129,  45], [223, 194, 125], [246, 232, 195],
                        [245, 245, 245], [199, 234, 229], [128, 205, 193],  [53, 151, 143], [1, 102, 94]]
cmap.precip_9   = create_colormap (cmap.colors_precip_9, reverse=False, name='precip_9'  )
cmap.precip_9_r = create_colormap (cmap.colors_precip_9, reverse=True , name='precip_9_r')

# Precip 10 colors
cmap.colors_precip_10 = [[ 84,  48,   5], [140,  81,  10], [191, 129,  45], [223, 194, 125], [246, 232, 195],
                         [199, 234, 229], [128, 205, 193],  [53, 151, 143], [1, 102, 94], [0, 60, 48]]
cmap.precip_10   = create_colormap (cmap.colors_precip_10, reverse=False, name='precip_10'  )
cmap.precip_10_r = create_colormap (cmap.colors_precip_10, reverse=True , name='precip_10_r')

# Precip 11 colors
cmap.colors_precip_11 = [[ 84,  48,   5], [140,  81,  10], [191, 129,  45], [223, 194, 125], [246, 232, 195],
                         [245, 245, 245], [199, 234, 229], [128, 205, 193], [ 53, 151, 143], [  1, 102,  94], [0, 60, 48]]
cmap.precip_11   = create_colormap (cmap.colors_precip_11, reverse=False, name='precip_11'  )
cmap.precip_11_r = create_colormap (cmap.colors_precip_11, reverse=True , name='precip_11_r')

# Precip continous
cmap.precip   = create_colormap (cmap.colors_precip_11, reverse=False, name='precip'  , continuous=True)
cmap.precip_r = create_colormap (cmap.colors_precip_11, reverse=True , name='precip_r', continuous=True)

# Temp 5 cmap.colors
cmap.colors_temp_5 = [[ 5, 113, 176], [146, 197, 222], [247, 247, 247], [244, 165, 130], [202, 0,  32]]
cmap.temp_5   = create_colormap (cmap.colors_temp_5, reverse=False, name='temp_5'  )
cmap.temp_5_r = create_colormap (cmap.colors_temp_5, reverse=True , name='temp_5_r')

# Temp 6 colors
cmap.colors_temp_6 = [[ 33, 102, 172], [103, 169, 207], [209, 229, 240], [253, 219, 199], [239, 138,  98], [178,  24,  43]]
cmap.temp_6   = create_colormap (cmap.colors_temp_6, reverse=False, name='temp_6'  )
cmap.temp_6_r = create_colormap (cmap.colors_temp_6, reverse=True , name='temp_6_r')

# Temp 7 colors
cmap.colors_temp_7 = [[33, 102, 172], [103, 169, 207], [209, 229, 240], [247, 247, 247],
                      [253, 219, 199], [239, 138,  98], [178,  24,  43]]
cmap.temp_7   = create_colormap (cmap.colors_temp_7, reverse=False, name='temp_7'  )
cmap.temp_7_r = create_colormap (cmap.colors_temp_7, reverse=True , name='temp_7_r')

# Temp 8 colors
cmap.colors_temp_8 = [[ 33, 102, 172],  [67, 147, 195], [146, 197, 222], [209, 229, 240], 
                      [253, 219, 199], [244, 165, 130], [214,  96,  77], [178,  24,  43]]
cmap.temp_8   = create_colormap (cmap.colors_temp_8, reverse=False, name='temp_8'  )
cmap.temp_8_r = create_colormap (cmap.colors_temp_8, reverse=True , name='temp_8_r')

# Temp 9 colors
cmap.colors_temp_9 = [[ 33, 102, 172], [67, 147, 195], [146, 197, 222], [209, 229, 240], [247, 247, 247],
                      [253, 219, 199], [244, 165, 130], [214,  96,  77], [178,  24, 43]]
cmap.temp_9   = create_colormap (cmap.colors_temp_9, reverse=False, name='temp_9'  )
cmap.temp_9_r = create_colormap (cmap.colors_temp_9, reverse=True , name='temp_9_r')

# Temp 10 colors
cmap.colors_temp_10 = [[5,  48,  97], [33, 102, 172], [67, 147, 195], [146, 197, 222], [209, 229, 240],
                       [253, 219, 199], [244, 165, 130], [214,  96,  77], [178,  24, 43], [103,   0,  31]]
cmap.temp_10   = create_colormap (cmap.colors_temp_10, reverse=False, name='temp_10'  )
cmap.temp_10_r = create_colormap (cmap.colors_temp_10, reverse=True , name='temp_10_r')

# Temp 11 colors
cmap.colors_temp_11 = [[  5,  48,  97], [ 33, 102, 172], [ 67, 147, 195], [146, 197, 222], [209, 229, 240],
                       [247, 247, 247], [253, 219, 199], [244, 165, 130], [214,  96,  77], [178,  24,  43], [103,   0,  31]]
cmap.temp_11   = create_colormap (cmap.colors_temp_11, reverse=False, name='temp_11'  )
cmap.temp_11_r = create_colormap (cmap.colors_temp_11, reverse=True , name='temp_11_r')

# Temp continous
cmap.temp   = create_colormap (cmap.colors_temp_11, reverse=False, name='temp_r', continuous=True)
cmap.temp_r = create_colormap (cmap.colors_temp_11, reverse=True , name='temp'  , continuous=True)

# Single Hue Blue 3 colors
cmap.colors_Blue_3 = [[222, 235, 247], [158, 202, 225], [49, 130, 189]]
cmap.Blue_3   = create_colormap (cmap.colors_Blue_3, reverse=False, name='Blue_3'  )
cmap.Blue_3_r = create_colormap (cmap.colors_Blue_3, reverse=True , name='Blue_3_r')

# Single Hue Blue 4 colors
cmap.colors_Blue_4 = [[239, 243, 255], [189, 215, 231], [107, 174, 214], [33, 113, 181]]
cmap.Blue_4   = create_colormap (cmap.colors_Blue_4, reverse=False, name='Blue_4'  )
cmap.Blue_4_r = create_colormap (cmap.colors_Blue_4, reverse=True , name='Blue_4_r')

# Single Hue Blue 5 colors
cmap.colors_Blue_5 = [[239, 243, 255], [189, 215, 231], [107, 174, 214], [49, 130, 189], [8, 81, 156]]
cmap.Blue_5   = create_colormap (cmap.colors_Blue_5, reverse=False, name='Blue_5'  )
cmap.Blue_5_r = create_colormap (cmap.colors_Blue_5, reverse=True , name='Blue_5_r')

# Single Hue Purple 3 colors
cmap.colors_Purple_3 = [[239, 237, 245], [188, 189, 220], [117, 107, 177]]
cmap.Purple_3   = create_colormap (cmap.colors_Purple_3, reverse=False, name='Purple_3'  )
cmap.Purple_3_r = create_colormap (cmap.colors_Purple_3, reverse=True , name='Purple_3_r')

# Single Hue Purple 4 colors
cmap.colors_Purple_4 = [[242, 240, 247], [203, 201, 226], [158, 154, 200], [106, 81, 163]]
cmap.Purple_4   = create_colormap (cmap.colors_Purple_4, reverse=False, name='Purple_4'  )
cmap.Purple_4_r = create_colormap (cmap.colors_Purple_4, reverse=True , name='Purple_4_r')

# Single Hue Purple 5 colors
cmap.colors_Purple_5 = [[242, 240, 247], [203, 201, 226], [158, 154, 200], [117, 107, 177], [84, 39, 143]]
cmap.Purple_5   = create_colormap (cmap.colors_Purple_5, reverse=False, name='Purple_5'  )
cmap.Purple_5_r = create_colormap (cmap.colors_Purple_5, reverse=True , name='Purple_5_r')

# Single Hue Red 3 colors
cmap.colors_Red_3 = [[254, 224, 210], [252, 146, 116], [222, 45, 38]]
cmap.Red_3   = create_colormap (cmap.colors_Red_3, reverse=False, name='Red_3'  )
cmap.Red_3_r = create_colormap (cmap.colors_Red_3, reverse=True , name='Red_3_r')

# Single Hue Red 4 colors
cmap.colors_Red_4 = [[254, 229, 217], [252, 174, 145], [251, 106, 74], [203, 24, 29]]
cmap.Red_4   = create_colormap (cmap.colors_Red_4, reverse=False, name='Red_4'  )
cmap.Red_4_r = create_colormap (cmap.colors_Red_4, reverse=True , name='Red_4_r')

# Single Hue Red 5 colors
cmap.colors_Red_5 = [[254, 229, 217], [252, 174, 145], [251, 106, 74], [222, 45, 38], [165, 15, 21]]
cmap.Red_5   = create_colormap (cmap.colors_Red_5, reverse=False, name='Red_5'  )
cmap.Red_5_r = create_colormap (cmap.colors_Red_5, reverse=True , name='Red_5_r')

# Single Hue Green 3 colors
cmap.colors_Green_3 = [[229, 245, 224], [161, 217, 155], [49, 163, 84]]
cmap.Green_3   = create_colormap (cmap.colors_Green_3, reverse=False, name='Green_3'  )
cmap.Green_3_r = create_colormap (cmap.colors_Green_3, reverse=True , name='Green_3_r')

# Single Hue Green 4 colors
cmap.colors_Green_4 = [[237, 248, 233], [186, 228, 179], [116, 196, 118], [35, 139, 69]]
cmap.Green_4   = create_colormap (cmap.colors_Green_4, reverse=False, name='Green_4'  )
cmap.Green_4_r = create_colormap (cmap.colors_Green_4, reverse=True , name='Green_4_r')

# Single Hue Green 5 colors
cmap.colors_Green_5 = [[237, 248, 233], [186, 228, 179], [116, 196, 118], [49, 163, 84], [0, 109, 44]]
cmap.Green_5   = create_colormap (cmap.colors_Green_5, reverse=False, name='Green_5'  )
cmap.Green_5_r = create_colormap (cmap.colors_Green_5, reverse=True , name='Green_5_r')

# Multi Hue YlBl 3 colors
cmap.colors_YlBl_3=[237, 248, 177, 127, 205, 187, 44, 127, 184]
cmap.YlBl_3   = create_colormap (cmap.colors_YlBl_3, reverse=False, name='YlBl_3'  )
cmap.YlBl_3_r = create_colormap (cmap.colors_YlBl_3, reverse=True , name='YlBl_3_r')

# Multi Hue YlBl 4 colors
cmap.colors_YlBl_4 = [[255, 255, 204], [161, 218, 180], [65, 182, 196], [34, 94, 168]]
cmap.YlBl_3   = create_colormap (cmap.colors_YlBl_4, reverse=False, name='YlBl_4'  )
cmap.YlBl_3_r = create_colormap (cmap.colors_YlBl_4, reverse=True , name='YlBl_4_r')

# Multi Hue YlBl 5 colors
cmap.colors_YlBl_5 = [[255, 255, 204], [161, 218, 180], [65, 182, 196], [44, 127, 184], [37, 52, 148]]
cmap.YlBl_5   = create_colormap (cmap.colors_YlBl_5, reverse=False, name='YlBl_5'  )
cmap.YlBl_5_r = create_colormap (cmap.colors_YlBl_5, reverse=True , name='YlBl_5_r')

# Multi Hue BlPr 3 colors
cmap.colors_BlPr_3 = [[224, 236, 244], [158, 188, 218], [136, 86, 167]]
cmap.BlPr_3   = create_colormap (cmap.colors_BlPr_3, reverse=False, name='BlPr_3'  )
cmap.BlPr_3_r = create_colormap (cmap.colors_BlPr_3, reverse=True , name='BlPr_3_r')

# Multi Hue BlPr 4 colors
cmap.colors_BlPr_4 = [[237, 248, 251], [179, 205, 227], [140, 150, 198], [136, 65, 157]]
cmap.BlPr_4   = create_colormap (cmap.colors_BlPr_4, reverse=False, name='BlPr_4'  )
cmap.BlPr_4_r = create_colormap (cmap.colors_BlPr_4, reverse=True , name='BlPr_4_r')

# Multi Hue BlPr 5 colors
cmap.colors_BlPr_5 = [[237, 248, 251], [179, 205, 227], [140, 150, 198], [136, 86, 167], [129, 15, 124]]
cmap.BlPr_5   = create_colormap (cmap.colors_BlPr_5, reverse=False, name='BlPr_5'  )
cmap.BlPr_5_r = create_colormap (cmap.colors_BlPr_5, reverse=True , name='BlPr_5_r')

# Multi Hue YlRd 3 colors
cmap.colors_YlRd_3 = [[254, 237, 160], [254, 178, 76], [240, 59, 32]]
cmap.YlRd_3   = create_colormap (cmap.colors_YlRd_3, reverse=False, name='YlRd_3'  )
cmap.YlRd_3_r = create_colormap (cmap.colors_YlRd_3, reverse=True , name='YlRd_3_r')

# Multi Hue YlRd 4 colors
cmap.colors_YlRd_4 = [[255, 255, 178], [254, 204, 92], [253, 141, 60], [227, 26, 28]]
cmap.YlRd_4   = create_colormap (cmap.colors_YlRd_4, reverse=False, name='YlRd_4'  )
cmap.YlRd_4_r = create_colormap (cmap.colors_YlRd_4, reverse=True , name='YlRd_4_r')

# Multi Hue YlRd 5 colors
cmap.colors_YlRd_5 = [[255, 255, 178], [254, 204, 92], [253, 141, 60], [240, 59, 32], [189, 0, 38]]
cmap.YlRd_5   = create_colormap (cmap.colors_YlRd_5, reverse=False, name='YlRd_5'  )
cmap.YlRd_5_r = create_colormap (cmap.colors_YlRd_5, reverse=True , name='5_r')

# Multi Hue YlGr 3 colors
cmap.colors = [[247, 252, 185], [173, 221, 142], [49, 163, 84]]
cmap.YlGr_3   = create_colormap (cmap.colors, reverse=False, name='YlGr_3'  )
cmap.YlGr_3_r = create_colormap (cmap.colors, reverse=True , name='YlGr_3_r')

# Multi Hue YlGr 4 colors
cmap.colors = [[255, 255, 204], [194, 230, 153], [120, 198, 121], [35, 132, 67]]
cmap.YlGr_4   = create_colormap (cmap.colors, reverse=False, name='YlGr_4'  )
cmap.YlGr_4_r = create_colormap (cmap.colors, reverse=True , name='YlGr_4_r')

# Multi Hue YlGr 5 colors
cmap.colors = [[255, 255, 204], [194, 230, 153], [120, 198, 121], [49, 163, 84], [0, 104, 55]]
cmap.YlGr_5   = create_colormap (cmap.colors, reverse=False, name='YlGr_5'  )
cmap.YlGr_5_r = create_colormap (cmap.colors, reverse=True , name='YlGr_5_r')

# Append mono colors for categories
cmap.colors_MultiCat_3 = []
cmap.colors_MultiCat_3.extend (cmap.colors_Purple_5[2:])
cmap.colors_MultiCat_3.extend (cmap.colors_Blue_5  [2:])
cmap.colors_MultiCat_3.extend (cmap.colors_Green_5 [2:])
cmap.colors_MultiCat_3.extend (cmap.colors_Red_5   [2:])
cmap.MultiCat_3   = create_colormap (cmap.colors_MultiCat_3, reverse=False, name='MultiCat_3'  )
cmap.MultiCat_3_r = create_colormap (cmap.colors_MultiCat_3, reverse=True , name='MultiCat_3_r')

cmap.colors_MultiCat_4 = []
cmap.colors_MultiCat_4.extend (cmap.colors_Purple_5[1:])
cmap.colors_MultiCat_4.extend (cmap.colors_Blue_5  [1:])
cmap.colors_MultiCat_4.extend (cmap.colors_Green_5 [1:])
cmap.colors_MultiCat_4.extend (cmap.colors_Red_5   [1:])
cmap.MultiCat_4   = create_colormap (cmap.colors_MultiCat_4, reverse=False, name='MultiCat_4'  )
cmap.MultiCat_4_r = create_colormap (cmap.colors_MultiCat_4, reverse=True , name='MultiCat_4_r')

cmap.colors_MultiCat_5 = []
cmap.colors_MultiCat_5.extend (cmap.colors_Purple_5)
cmap.colors_MultiCat_5.extend (cmap.colors_Blue_5  )
cmap.colors_MultiCat_5.extend (cmap.colors_Green_5 )
cmap.colors_MultiCat_5.extend (cmap.colors_Red_5   )
cmap.MultiCat_5   = create_colormap (cmap.colors_MultiCat_5, reverse=False, name='MultiCat_5'  )
cmap.MultiCat_5_r = create_colormap (cmap.colors_MultiCat_5, reverse=True , name='MultiCat_5_r')
