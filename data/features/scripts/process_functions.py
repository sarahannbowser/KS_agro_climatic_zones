# -*- coding: utf-8 -*-
"""
Created on Sun Aug  7 17:30:21 2022

@author: sarahann
"""
import numpy as np
from osgeo import gdal, ogr, osr
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
import fiona


def reproject_file(filename,file_str, new_crs):
    """" Function to reproject a raster file to a new crs"""
    new_filename = 'C:/Users/sarahann.USERS/Desktop/code/ks_agro_climate/'+file_str+'_wgs84.tif'
    with rasterio.open(filename) as src:
        transform, width, height = calculate_default_transform(
            src.crs, new_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': new_crs,# dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })

        with rasterio.open(new_filename, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs= new_crs,#dst_crs,
                    resampling=Resampling.nearest)
                

def crop_to_shape(filename, file_str):
    """" Function to crop a raster file to the outer most bounds of another raster file."""
    clipped_filename = 'C:/Users/sarahann.USERS/Desktop/code/ks_agro_climate/'+file_str+'_wgs84_ks.tif'
    ks_vector_filename = 'C:/Users/sarahann.USERS/Desktop/scripts_jp/agroecology_paper/data_processing/ks_shp/ks_map.shp'
    with fiona.open(ks_vector_filename, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    
    raster = rasterio.open(filename) # To see the properties use paws.meta
    img, transform = mask(raster, shapes, crop=True)

    profile = {'driver': 'GTiff',
               'dtype': 'float32',
               'nodata': -9999.0,
               'width': img.shape[2],
               'height': img.shape[1],
               'count': img.shape[0],
               'crs': raster.crs,
               'transform': transform}

    with rasterio.open(clipped_filename, 'w', **profile) as f:
        f.write(np.squeeze(img),1)

 
def rescale_map(filename, file_str, new_width, new_height, method):
    """" Function to scale a raster file to a common grid"""
    filename_scaled = 'C:/Users/sarahann.USERS/Desktop/code/ks_agro_climate/'+file_str+'_wgs84_ks_scaled.tif'
    with rasterio.open(filename) as src:

        # resample data to target shape
        img = src.read(out_shape=(src.count,new_height, new_width), resampling=Resampling[method])

        # scale image transform
        transform = src.transform * src.transform.scale((src.width/new_width), (src.height/new_height))

        profile = {'driver': 'GTiff',
                   'dtype': 'float32',
                   'nodata': -9999.0,
                   'width': new_width,
                   'height': new_height,
                   'count': img.shape[0],
                   'crs': src.crs,
                   'transform': transform}

        with rasterio.open(filename_scaled, 'w', **profile) as f:
            f.write(np.squeeze(img),1)
            

def array2raster(file_str,rasterfn,array):
    """" Function to convert an array to a raster file"""
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    cols = array.shape[1]
    rows = array.shape[0]

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(file_str, cols, rows, 1, gdal.GDT_Byte)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


# Function to open each file, and save to a vector data format/shape file
def rast2vec(path, string):
    """" Function to convert a raster file to a shape file"""
    prism_ds = gdal.Open(path)                      
    band = prism_ds.GetRasterBand(1)
    drv = ogr.GetDriverByName('ESRI Shapefile')

    # customer out path, and file name
    outfile = drv.CreateDataSource(r'C:/Users/sarahann.USERS/Desktop/code/ks_agro_climate/'+ string +'.shp') 
    outlayer = outfile.CreateLayer('polygonized raster', srs = None )  
    newField = ogr.FieldDefn(string, ogr.OFTReal)            #custom variable name
    outlayer.CreateField(newField)

    gdal.Polygonize(band, None, outlayer, 0, [])
    outfile = None
