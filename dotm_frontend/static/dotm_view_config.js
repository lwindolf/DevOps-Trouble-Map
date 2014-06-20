/* Simle view that generates HTML forms and fills values from JSON */

function printConfigForm(key, setting) {
	var result = "<div class='settingsForm'>";
	result += "<div class='title'>"+setting.title+"</div>";
	result += "<div class='description'>"+setting.description+"</div>";
	result += "<form action='settings/"+key+"' method='POST'>";
	if(setting.type == 'single_value') {
		result += "<input type='text' value='"+(setting.values?setting.values:"")+"'/>";
		result += "<input type='submit' value='Save'/>";
	}
	if(setting.type == 'array') {
		result += "<table>";
		result += "<tr><th>"+setting.fields[0]+"</th></tr>";
		$.each(setting.values, function(index, value) {
			result += "<tr><td>";
			result += "<input type='text' name='key' value='"+value+"' readonly/>";
			result += "<input type='button' value='Remove'/>";
			result += "</td></tr>";
		});
		result += "</table>";
		if(setting.add) {
			result += "<table>";
			result += "<tr><th>"+setting.fields[0]+"</th></tr>";
			result += "<tr><td>";
			result += "<input type='text' name='key' value=''/>";
			result += "<input type='button' value='Add'/>";
			result += "</td></tr>";
			result += "</table>";
		}
	}
	if(setting.type == 'hash') {
		result += "<table>";
		result += "<tr><th>"+setting.fields[0]+"</th><th>"+setting.fields[1]+"</th></tr>";
		$.each(setting.values, function(key, value) {
			result += "<tr><td>";
			result += "<input type='text' name='key' value='"+key+"' readonly/>";
			result += "</td><td>";
			result += "<input type='text' name='value' value='"+value+"'/>";
			if(setting.add)
				result += "<input type='button' value='Remove'/>";
			result += "</td></tr>";
		});
		result += "</table>";
		if(setting.add) {
			result += "<table>";
			result += "<tr><th>"+setting.fields[0]+"</th><th>"+setting.fields[1]+"</th></tr>";
			result += "<tr><td>";
			result += "<input type='text' name='key' value=''/>";
			result += "</td><td>";
			result += "<input type='text' name='value' value=''/>";
			result += "<input type='button' value='Add'/>";
			result += "</td></tr>";
			result += "</table>";
		}
	}
	result += "</form>";
	result += "</div>";
	return result;
}

function loadConfig() {
	// Clean everything
	setStatus('Fetching settings...');
	// FIXME: Use a stage div instead of nodeChart!
	$(".nodeChart").html("");
	$("#nodeTables").hide();

	$.getJSON("backend/settings", {})
	.done(function (data) {
		var forms = "";

		$.each(data, function(key, setting) {
			forms += printConfigForm(key, setting);
		});

		$(".nodeChart").html(forms);

		setStatus("Settings loaded.");
	})
	.fail(function (jqxhr, textStatus, error) {
		setError('Fetching settings failed! ('+error+')');
	})
}
