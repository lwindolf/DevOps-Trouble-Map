/* DOTM view displaying all external IPs and resolvable names with a
   popup bubble presenting IP and faulty services */

function DOTMViewGMap(stage) {
	this.stage = stage;
	this.selectedNode = null;
	this.reload();
}

function dotm_view_gmap_render_services (data) {
        if (!data)
                return "";

        if (!data['services_alerts'])
                return "";

        var result = "";
        $.each(data['services_alerts'], function(service, status) {
                result += " <span class='service status_"+status+"'> " + service + " </span>";
        });

        return result;
}

DOTMViewGMap.prototype.setData = function(locations) {
	// Clean everything
	clearStatus(this.stage);
	$(this.stage).html("<div id='gmap'></div>");

	// Add marker icons to locations list
	$.each(locations, function(index, location) {
		try {
			/* Merge maximum node and service status */
			var status = location.data.monitoring.status;
			$.each(location.data.monitoring.services_alerts, function(service, service_status) {
				if(service_status == 'WARNING' && status != "DOWN")
					status = 'WARNING';
				if(service_status == 'CRITICAL')
					status = 'DOWN';
			});

			location['options'] = new Array();
			if(status == 'UP')
				location['options']['icon'] = 'http://maps.google.com/mapfiles/marker_green.png';
			else if(status == 'DOWN')
				location['options']['icon'] = 'http://maps.google.com/mapfiles/marker.png';
			else
				location['options']['icon'] = 'http://maps.google.com/mapfiles/marker_orange.png';

		} catch(e) {
		}
	});

	$("#gmap").gmap3({
		map:{
			options: {
				zoom:3,
				mapTypeId: google.maps.MapTypeId.SATELLITE,
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


DOTMViewGMap.prototype.reload = function() {
	var view = this;

	$.getJSON("backend/geo/nodes", {})
	.done(function (data) {
		view.setData(data.locations);
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Node geo locations fetch failed! ('+error+')');
	});
}
