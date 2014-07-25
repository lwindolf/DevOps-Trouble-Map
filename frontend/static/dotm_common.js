
var timeouts = new Array();

function setStatus(id, text) {
	var statusBox = $(id).parent().find('.status');

	statusBox
	.addClass('normal')
	.removeClass('error')
	.html(text);

	if(timeouts[id])	
		clearTimeout(timeouts[id]);

	timeouts[id] = setTimeout(function() {
        	statusBox.hide('blind', {}, 500)
	}, 5000);
}

function setError(id, text) {
	$(id)
	.parent()
	.find('.status')
	.removeClass('normal')
	.addClass('error')
	.html(text);

	if(timeouts[id])	
		clearTimeout(timeouts[id]);
}

function clearStatus(id) {
	$(id)
	.parent()
	.find('.status')
	.removeClass('normal')
	.removeClass('error')
	.html('');
}

// Print a node name with optional link
function nodeLink(node) {
	var re = /^[0-9.]+$/;
	if(node != "Internet" && !re.test(node)) {
		return "<a href='javascript:loadNode(\""+node+"\");'>"+node+"</a>";
	}
	return node;
}

