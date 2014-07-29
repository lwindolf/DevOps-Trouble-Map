function dotm_view_gmap_render_services (data) {
        if (!data)
                return "";

        if (!data['services'])
                return "";

        var result = "";
        for (var i = 0; i < data['services'].length; i++) {
		var s = data['services'][i];
		if (s['status'] != 'OK')
	                result += " <span class='service status_"+s['status']+"'> " + s['service'] + " </span>";
        }

        return result;
}

function loadGMap(stage, locations) {
	// Clean everything
	clearStatus(stage);
	$(stage).html("<div id='gmap'></div>");

	// Add marker icons to locations list
	$.each(locations, function(index, ip) {
		try {
			/* Merge maximum node and service status */
			var status = ip.data.monitoring.node.status;
			$.each(ip.data.monitoring.services, function(index, s) {
				if(s['status'] == 'WARNING' && status != "DOWN")
					status = s['status'];
				if(s['status'] == 'CRITICAL')
					status = "DOWN";
			});

			ip['options'] = new Array();
			if(status == 'UP')
				ip['options']['icon'] = 'http://maps.google.com/mapfiles/marker_green.png';
			else if(status == 'DOWN')
				ip['options']['icon'] = 'http://maps.google.com/mapfiles/marker.png';
			else
				ip['options']['icon'] = 'http://maps.google.com/mapfiles/marker_orange.png';

		} catch(e) {
		}
	});

	$("#gmap").gmap3({
		map:{
			options: {
				zoom:3
			}
		},
		marker:{
			values:locations,
			options: {
				icon: new google.maps.MarkerImage('http://maps.google.com/mapfiles/marker_grey.png')
			},
		events:{
		      click: function(marker, event, context){
			loadNode(context.data.node);
		      },
		      mouseover: function(marker, event, context){
			$(this).gmap3(
			  {clear:"overlay"},
			  {
			  overlay:{
			    latLng: marker.getPosition(),
			    options:{
			      content:  "<div class='mapbullet'>" +
				          "<div class='text'>" + context.data.node + 
                                          " (" + context.data.ip + ")" +
                                          dotm_view_gmap_render_services (context.data['monitoring']) +
					  "</div>" +
				        "</div>",
			      offset: {
				x:-46,
				y:-73
			      }
			    }
			  }
			});
		      },
		      mouseout: function(){
			$(this).gmap3({clear:"overlay"});
		      }
	  	}
		}
	});

	/* Autofit if >1 marker (with 1 marker only too deep zoom in) */
	if(locations.length > 1)
		$("#gmap").gmap3('autofit');
}

