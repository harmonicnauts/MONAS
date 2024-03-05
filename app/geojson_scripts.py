# Function for adding some properties to all the points in Leaflet Map
from dash_extensions.javascript import assign

on_each_feature = assign(
    """function(feature, layer, context){
        if(feature.properties.lokasi){
            var tooltipContent = `
                <div 
                    style='
                    border: 1px solid black;
                    border-radius: 5px;
                    font-size: 13.5px;
                    padding : 3px;'
                    >
                    <img style = 'width : 20px' src="https://cdn.bmkg.go.id/Web/Logo-BMKG-new.png"/>
                    <strong>${feature['properties']['Nama UPT']}</strong><br>
                    <p>Kode: ${feature['properties']['lokasi']}</p>
                    <p>Koord: (${feature['properties']['LAT']}, ${feature['properties']['LON']})</p>
                    <!--<p>Temperature : <span style = 'color: red'; >${feature['properties']['mean_temp 0']}</span> C</p>-->
                    <!--<p>Relative Humidity : <span style = 'color: blue'; >${feature['properties']['mean_humidity 0']}</span>%</p>-->
                    <!--<p>Precipitation : <span style = 'color: purple';>${feature['properties']['mean_precipitation 0']}</span>mm.</p>-->
                    <table>
                        <thead>
                            <tr>
                                <th></th>
                                <th>Max Value</th>
                                <th>Mean Value</th>
                                <th>Min Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Temperature</td>
                                <td>${feature['properties']['max_temp']}</td>
                                <td>${feature['properties']['mean_temp']}</td>
                                <td>${feature['properties']['min_temp']}</td>
                            </tr>
                            <tr>
                                <td>Humidity</td>
                                <td>${feature['properties']['max_humidity']}</td>
                                <td>${feature['properties']['mean_humidity']}</td>
                                <td>${feature['properties']['min_humidity']}</td>
                            </tr>
                            <tr>
                                <td>Precipitation</td>
                                <td>${feature['properties']['max_precipitation']}</td>
                                <td>${feature['properties']['mean_precipitation']}</td>
                                <td>${feature['properties']['min_precipitation']}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                `;
            layer.bindTooltip(tooltipContent, { sticky: true });
        }
    }
    """)



# Function for assignng circlemarkers to each point
point_to_layer = assign(
    """
    function(feature, latlng, context){
        const {min, max, colorscale, circleOptions, colorProp} = context.hideout;
        const csc = chroma.scale(colorscale).domain([min, max]);  // chroma lib to construct colorscale
        circleOptions.fillColor = csc(feature.properties[colorProp]);  // set color based on color prop
        return L.circleMarker(latlng, circleOptions);  // render a simple circle marker
    }
    """)