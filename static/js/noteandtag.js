$(document).ready(function() {
	let body = $("body");
	let api_base_url = body.attr("data-api-base-url");
	let cdn_url = body.attr("data-cdn-url");

	var TagsUI = function(root, api_base_url) {
		this._root = root
		this._root.html("");
		this._api_base_url = api_base_url
		this._selection_changed = $.Callbacks();
	};
	
	TagsUI.prototype = {
		selection_changed: function(cb)
		{
			this._selection_changed.add(cb);
		},
		_on_tag_clicked: function(name)
		{
			this._root.find(`.nat-tag[data-name='${name}']`).toggleClass("nat-tag-selected");
			let tags = $.makeArray(this._root.find(".nat-tag-selected .nat-tag-name"));
			this._selection_changed.fire(tags.map(o => $(o).text()));
		},
		_display: function(tags)
		{
			this._root.html("");
			tags.forEach(tag => {
				let element = $("<a>", {'class': 'nat-tag', 'href': '#', 'data-name': tag["name"]}).append(
					$("<span>", {'class': 'nat-tag-name', 'text': tag["name"]}),
					$("<span>", {'class': 'nat-tag-total', 'text': tag["total"]}),
				);
				element.click(() => this._on_tag_clicked(tag["name"]));
				this._root.append(element);
			});
		},
		query: function() {
			$.ajax({
				url: this._api_base_url + "tags",
				type: "GET",
				contentType: "application/json",
				dataType: "json",
				success: (response) => {
					if (response["result"] != "Ok")
					{
						console.log(response["error"]);
					}
					else
					{
						this._display(response["params"]);
					}
				}
			});
		}
	};

	var NotesUI = function(root, api_base_url) {
		this._root = root
		this._root.html("");
		this._api_base_url = api_base_url
	};
	
	NotesUI.prototype = {
		_display: function(notes)
		{
		console.log(notes);
			this._root.html("");
			notes.forEach(note => {
				let element = $("<div>", {'class': 'nat-note', 'data-id': note["id"]}).append(
					$("<div>", {'class': 'nat-note-label', 'text': note["label"]}),
					$("<div>", {'class': 'nat-note-body', 'text': note["body"]}),
				);
				this._root.append(element);
			});
		},
		query: function(tags) {
			let url = this._api_base_url + "notes/"
			console.log(tags);
			if (tags !== undefined) {
				url += tags.join(":");
			}
	
			$.ajax({
				url: url,
				type: "GET",
				contentType: "application/json",
				dataType: "json",
				success: (response) => {
					if (response["result"] != "Ok")
					{
						console.log(response["error"]);
					}
					else
					{
						this._display(response["params"]);
					}
				}
			});
		}
	};

	let notes = new NotesUI($("#nat-notes"), api_base_url);
	let tags = new TagsUI($("#nat-tags"), api_base_url);

	tags.selection_changed((tags) => notes.query(tags));
	tags.query();
	notes.query();
});
