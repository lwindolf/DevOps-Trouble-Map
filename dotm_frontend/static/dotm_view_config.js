/* Simle view that generates HTML forms and fills values from JSON */

function printConfigForm(key, setting) {
	var result = "<div class='settingsForm'>";
	result += "<div class='title'>"+setting.title+"</div>";
	result += "<div class='description'>"+setting.description+"</div>";
	if(setting.type == 'single_value') {
		result += "<form action='backend/settings/set/"+key+"' method='POST'>";
		result += "<input type='text' value='"+(setting.values?setting.values:"")+"'/>";
		result += "<input type='submit' value='Save'/>";
		result += "</form>";
	}
	if(setting.type == 'array') {
		result += "<table>";
		result += "<tr><th>"+setting.fields[0]+"</th></tr>";
		$.each(setting.values, function(index, value) {
			result += "<tr><td>";
			result += "<form action='backend/settings/remove/"+key+"' method='POST'>";
			result += "<input type='text' name='key' value='"+value+"' readonly/>";
			result += "<input type='submit' value='Remove'/>";
			result += "</form>";
			result += "</td></tr>";
		});
		result += "</table>";
		result += "<table>";
		result += "<tr><th>"+setting.fields[0]+"</th></tr>";
		result += "<tr><td>";
		result += "<form action='backend/settings/add/"+key+"' method='POST'>";
		result += "<input type='text' name='value' value=''/>";
		result += "<input type='submit' value='Add'/>";
		result += "</form>";
		result += "</td></tr>";
		result += "</table>";
	}
	if(setting.type == 'hash') {
		/* There can be two hash variants. One used for providing
		   lists of tuples, which you can remove or add (no editing
		   for simplicity). And one type used to provide values for
		   fixed hash keys (defined by defaults) which you can set only. */

		if(setting.add) {
			/* Variant 1: tuple list */
			result += "<table>";
			result += "<tr><th>"+setting.fields[0]+"</th><th>"+setting.fields[1]+"</th></tr>";
			$.each(setting.values, function(k, value) {
				result += "<tr><td>";
				result += "<input type='text' name='key' value='"+k+"' readonly/>";
				result += "</td><td>";
				result += "<form action='backend/settings/delHash/"+key+"' method='POST'>";
				result += "<input type='hidden' name='key' value='"+k+"' readonly/>";
				result += "<input type='text' name='value' value='"+value+"' readonly/>";
				if(setting.add)
					result += "<input type='submit' value='Remove'/>";
				result += "</form>";
				result += "</td></tr>";
			});
			result += "</table>";

			result += "<form action='backend/settings/setHash/"+key+"' method='POST'>";
			result += "<table>";
			result += "<tr><th>"+setting.fields[0]+"</th><th>"+setting.fields[1]+"</th></tr>";
			result += "<tr><td>";
			result += "<input type='text' name='key1' value=''/>";
			result += "</td><td>";
			result += "<input type='text' name='value1' value=''/>";
			result += "<input type='submit' value='Add'/>";
			result += "</td></tr>";
			result += "</table>";
			result += "</form>";
		} else {
			/* Variant 2: key-values */
			result += "<form action='backend/settings/setHash/"+key+"' method='POST'>";
			result += "<table>";
			result += "<tr><th>"+setting.fields[0]+"</th><th>"+setting.fields[1]+"</th></tr>";
			var i = 1;
			$.each(setting.values, function(key, value) {
				result += "<tr><td>";
				result += "<input type='text' name='key"+i+"' value='"+key+"' readonly/>";
				result += "</td><td>";
				var type='text';
				if(key == 'password')
					type='password';
				result += "<input type='"+type+"' name='value"+i+"' value='"+value+"'/>";
				result += "</td></tr>";
				i++;
			});
			result += "</table>";
			result += "<input type='submit' value='Save'/>";
			result += "</form>";
		}
	}
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
		var forms = new Array();;

		$.each(data, function(key, setting) {
			forms[setting.position] = printConfigForm(key, setting);
		});
		$.each(forms, function(position, html) {
			$(".nodeChart").append(html);
		});

		setStatus("Settings loaded.");
	})
	.fail(function (jqxhr, textStatus, error) {
		setError('Fetching settings failed! ('+error+')');
	})
}
