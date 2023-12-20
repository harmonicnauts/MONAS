window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, layer, context) {
                if (feature.properties.lokasi) {
                    var tooltipContent = `
                <div 
                    style='
                    border: 1px solid black;
                    border-radius: 5px;
                    font-size: 15px;
                    padding : 3px;'
                    >
                    <img style = 'width : 20px' src="https://cdn.bmkg.go.id/Web/Logo-BMKG-new.png"/>
                    <strong>${feature['properties']['Nama UPT']}</strong><br>
                    <p>Kode: ${feature['properties']['lokasi']}</p>
                    <p>Koord: (${feature['properties']['LAT']}, ${feature['properties']['LON']})</p>
                    <p>Temperature : <span style = 'color: red'; >${feature['properties']['mean_temp 0']}</span> C</p>
                    <p>Relative Humidity : <span style = 'color: blue'; >${feature['properties']['mean_humidity 0']}</span>%</p>
                    <p>Precipitation : <span style = 'color: purple';>${feature['properties']['mean_precipitation 0']}</span>mm.</p>
                </div>
                `;
                    layer.bindTooltip(tooltipContent, {
                        sticky: true
                    });
                }
            }

            ,
        function1: function(feature, latlng, context) {
            const {
                min,
                max,
                colorscale,
                circleOptions,
                colorProp
            } = context.hideout;
            const csc = chroma.scale(colorscale).domain([min, max]); // chroma lib to construct colorscale
            circleOptions.fillColor = csc(feature.properties[colorProp]); // set color based on color prop
            return L.circleMarker(latlng, circleOptions); // render a simple circle marker
        }

    }
});