
var timeouts = new Array();

function setStatus(id, text) {
	var statusBox = $(id).parent().find('.statusBox');

	statusBox
	.addClass('normal')
	.removeClass('warning')
	.removeClass('error')
	.html(text)
	.show();

	if(timeouts[id])	
		clearTimeout(timeouts[id]);

	timeouts[id] = setTimeout(function() {
        	statusBox.hide('blind', {}, 500)
	}, 5000);
}

function setWarning(id, text) {
	$(id)
	.parent()
	.find('.statusBox')
	.removeClass('normal')
	.removeClass('error')
	.addClass('warning')
	.html(text)
	.show();

	if(timeouts[id])	
		clearTimeout(timeouts[id]);
}

function setError(id, text) {
	$(id)
	.parent()
	.find('.statusBox')
	.removeClass('normal')
	.removeClass('warning')
	.addClass('error')
	.html(text)
	.show();

	if(timeouts[id])	
		clearTimeout(timeouts[id]);
}

function clearStatus(id) {
	$(id)
	.parent()
	.find('.statusBox')
	.removeClass('normal')
	.removeClass('warning')
	.removeClass('error')
	.html('test')
	.hide();

	if(timeouts[id])	
		clearTimeout(timeouts[id]);
}

// Print a node name with optional link
function nodeLink(node) {
	var re = /^[0-9.]+$/;
	if(node != "Internet" && !re.test(node)) {
		return "<a href='javascript:loadNode(\""+node+"\");'>"+node+"</a>";
	}
	return node;
}

