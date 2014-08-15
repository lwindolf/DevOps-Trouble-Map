/* Simple view that generates HTML forms and fills values from JSON */

function DOTMViewHistory(stage) {
	this.stage = stage;
}

DOTMViewHistory.prototype.reload = function() {
	var view = this;

	// Clean everything
	setStatus(this.stage, 'Fetching snapshot list...');
	$(this.stage).html("");

	$.getJSON("backend/history", {})
	.done(function (data) {
		var navigation, list = "";
		var selected = getHistoryIndex();
		var selectedIndex = -1;
		
		$.each(data.sort(), function(index, timestamp) {
			if(selected != "" && selected == timestamp)
				selectedIndex = index;

			list = "<div id='snapshot_"+timestamp+"' class='snapshot'>"+
				"<a class='"+((selectedIndex == index)?" selected":"")+"' href='javascript:setHistoryIndex(\""+timestamp+"\")'>"+
				new Date(timestamp*1000).toString()+
				"</a></div>" + list;
		});
		list = "<h3>List of Snapshots</h3><div class='history'>" + list;
		list += "</div></div>";

		if(selected != "" && selectedIndex == -1)
			setError(view.stage, "Invalid snapshot selection. Snapshot '"+selected+"' doesn't exist!");

		// Append navigation after we know about index of previous and next snapshot
		navigation = "<div class='settingsForm'>";

		if(selected != "")
			navigation +=
				"<p>" +
				"<input type='button' value='Reset to Live View' onclick='setHistoryIndex(\"\")'/>" +
				"</p><p>" +
				"<input type='button' value='&lt;&lt;&lt;' title='More Recent Snapshot' onclick='setHistoryIndex(\""+data[selectedIndex + 1]+"\")'"+
				((selectedIndex + 1 >= data.length)?" disabled":"")+"/>"+
				"<input type='button' value='>>>' title='Older Snapshot' onclick='setHistoryIndex(\""+data[selectedIndex - 1]+"\")'"+
				((selectedIndex - 1 < 0)?" disabled":"")+"/>"+
				"</p>";
		else
			navigation += "<p>Select a snapshot to view a past system state.</p>";

		$(view.stage).html(navigation + list);
		clearStatus(view.stage);
		$(".snapshot a.selected").css("background", "#ccc");
	})
	.fail(function (jqxhr, textStatus, error) {
		setError(view.stage, 'Fetching snapshot list failed! ('+error+')');
	})
}
