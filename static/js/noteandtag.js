$(document).ready(function() {
	let body = $("body");
	let api_base_url = body.attr("data-api-base-url");
	let cdn_url = body.attr("data-cdn-url");
	
	function setHeight(jq_in){
	    jq_in.each(function(index, elem){
	        // This line will work with pure Javascript (taken from NicB's answer):
	        elem.style.height = elem.scrollHeight+'px'; 
	    });
	}

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

	var NoteEditor = function(note_ui) {
		this.root = $("<div>", {'class': 'nat-note-editor'}).append(
			$("<div>", {'class': 'nat-note-editor-body'}).append(
				$("<textarea>", {'text': ''}),
				$("<div>", {'class': 'nat-note-editor-toolbar'}).append(
					$("<input>", {'type': 'button', 'value': "Save"}),
					$("<div>", {'style': 'clear: both;'})
				)
			)
		);
		this._note_ui = note_ui;
		this._widgets = {
			textarea: this.root.find("textarea").first(),
			save: this.root.find(".nat-note-editor-toolbar input").first()
		};
		this._widgets.textarea.change(() => this._resize_textarea());
		this._widgets.textarea.keyup(() => this._resize_textarea());
		this._widgets.textarea.keydown(() => this._resize_textarea());
		this._widgets.save.click(() => this._on_save_clicked());
		this._update_text();
	};
	
	NoteEditor.prototype = {
		_on_save_clicked: function() {
		    let data = jsyaml.load(this._widgets.textarea.val());
		    data["id"] = this._note_ui.data["id"];
		    console.log(data);

			$.ajax({
				url: api_base_url + "notes/" + data["id"],
				type: "POST",
				contentType: "application/json",
				dataType: "json",
				data: JSON.stringify({"data": data}),
				success: (response) => {
					if (response["result"] != "Ok")
					{
						alert(response["error"]);
					}
					else
					{
						this._note_ui.update(data);
						this._on_saved();
					}
				}
			});
		},
		_on_saved: function() {
			this.root.remove();
			this._note_ui.show();
		},
		_resize_textarea: function() {
			this._widgets.textarea.css("height", this._widgets.textarea.prop("scrollHeight")+'px');
		},
		_update_text: function() {
			this._widgets.textarea.text(jsyaml.dump({
				label: this._note_ui.data["label"],
				body: this._note_ui.data["body"],
				tags: this._note_ui.data["tags"],
			}));
		}
	};

	var NoteUI = function(data) {
		this.root = $("<div>", {'class': 'nat-note', 'data-id': ''}).append(
			$("<div>", {'class': 'nat-note-head'}).append(
				$("<span>", {'class': 'nat-note-label', 'text': ''}),
				$("<div>", {'class': 'nat-note-toolbar'}).append(
					$("<button>", {'class': 'nat-note-edit', 'type': 'button'}).append(
						$("<img>", {'src': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/OOjs_UI_icon_edit-ltr.svg/20px-OOjs_UI_icon_edit-ltr.svg.png'})
					)
				)
			),
			$("<div>", {'class': 'nat-note-body', 'text': ''}),
		);
		this._widgets = {
			label: this.root.find(".nat-note-label").first(),
			body: this.root.find(".nat-note-body").first(),
			edit: this.root.find(".nat-note-edit").first()
		};
		this._widgets.edit.click(() => this._on_edit_clicked());
		this.update(data);
	};
	
	NoteUI.prototype = {
		_on_edit_clicked: function() {
			let editor = new NoteEditor(this);
			editor.root.insertBefore(this.root);
			this.hide();
		},
		hide: function() {
			this.root.addClass("nat-hidden");
		},
		show: function() {
			this.root.removeClass("nat-hidden");
		},
		update: function(data) {
			this.root.attr("data-id", data["id"]);
			this._widgets.label.html(data["label"]);
			this._widgets.body.html(data["body"]);
			this.data = data;
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
			this._root.html("");
			notes.forEach(note => {
				let widget = new NoteUI(note);
				this._root.append(widget.root);
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
