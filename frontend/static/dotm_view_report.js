/* Simple view that prints an problem report table */

function DOTMViewReport(stage) {
	this.stage = stage;
}

DOTMViewReport.prototype.reload = function() {
	var view = this;

	// Clean everything
	setStatus(this.stage, 'Fetching report...');
	$(this.stage).html("");

	$.getJSON("backend/report", {})
	.done(function (data) {
		try {
			var list = "";
			$.each(data.alerts, function(node, alerts) {
				$.each(alerts, function(index, alert) {
					list += "<tr class='service'>" +
						"<td class='category'>"+alert['category']+"</td>"+
						"<td class='node'>"+node+"</td>"+
						"<td class='service severity status_"+alert['severity']+"'>"+alert['severity']+"</td>"+
						"<td class='message'>"+alert['message']+"</td>"+
						"</tr>";
				});
			});
			list = "<div class='settingsForm'><h3>Problem Report</h3><table id='report' border='1'>" + list + "</table></div>";
			$(view.stage).html(list);
			clearStatus(view.stage);
		} catch(e) {
			setError(view.stage, 'Rendering report failed! ('+e+')');
		}
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Fetching report failed! ('+error+')');
	})
}
