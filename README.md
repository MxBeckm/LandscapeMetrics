# LandscapeMetrics
An ArcGis Python Toolbox for calculating proximity indices.

For my final project of the Application Development GIS course I developed a python Toolbox for ArcGis Pro. The toolbox can calculate four different Proximity Indices.
PX92 = A_t/d
PX94 = A_f/d+∑_(i=1)^n▒A_t/d
PXfg = ∑_(i=1)^n▒A_t/d²
PXpt = A_f/d

With A = Area , d = Distance to Nearest Neighbour, t = Target patch and f = focal patch.
The toolbox requires five input parameters to be specified before it is executable. The first being the Feature Class. The second is the index which should be calculated. The indices can be selected or deselected via clicking on the checkbox, allowing the user to choose multiple indices at once. The Third is the Buffer distance. This is the area, around the focal feature, which will be considered for calculation. The forth input is the Class Field, a column in the Feature Class which identifies features belonging to the same class. It is configured to be a dropdown list, showing the fields of the attribute table. Fifth, the Value of the Class Field. 
If each input parameter has a value, the script can be run. After running it the calculated indices will be added to the Feature Classes attribute table. The naming convention is “name of the index”+ “_” + “Buffer distance”. Furthermore three additional fields will be added. NNArea, NNDist and NNFID which are the area, distance and object ID of the nearest feature of the same class. 
The Toolbox has inline comments to better understand how it works and it has been uploaded to Github and is available under https://github.com/MxBeckm/LandscapeMetrics.
To add the Toolbox to ArcGis Pro, open a new project, goto Insert > Toolbox > Add Toolbox and select the .pyt file.
