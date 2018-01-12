import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
var Network = require('../network');

var Filter = React.createClass({

    componentDidMount: function(){
		var elem = this.refs[this.props.name], pos = elem.value.length;
		elem.focus();
		elem.setSelectionRange(pos, pos);
    },

    filter: function(e){
        this.props.dispatch({type: 'FILTER', filterBy: e.target.value});
    },

    render: function () {
        return (
            <Bootstrap.InputGroup>
                <input
                    id={this.props.name}
                    type="text"
                    className="form-control"
                    placeholder="Filter"
                    value={this.props.filter.filterBy}
                    onChange={this.filter}
                    ref={this.props.name}
                />
                <Bootstrap.InputGroup.Addon>
                  <Bootstrap.Glyphicon glyph="search" />
                </Bootstrap.InputGroup.Addon>
            </Bootstrap.InputGroup>
        );
    }
});

var Button = React.createClass({

    openModal: function() {
        var modal = this.props.modalTemplate;
        this.props.dispatch({type: 'OPEN_MODAL', template: modal});
    },

    showTarget: function(target) {
        console.log(target);
        this.props.dispatch({type: 'TOGGLE'});
    },

    btn_action: function(action) {
        var me = this;
        if("tblName" in this.props){
            var panel = this.props.panel;
            var filterVal = document.getElementById('reactableFilter').value;
            var data = {server_name: panel.server, panel: panel.panel, args: panel.args, table_name: this.props.tblName, filter_field: filterVal};
            Network.download_file('/api/panels/get_panel_pdf', this.props.auth.token, data).done(function(d) {
                var data = new Blob([d], {type: 'octet/stream'});
                var url = window.URL.createObjectURL(data);
                tempLink = document.createElement('a');
                tempLink.style = "display: none";
                tempLink.href = url;
                tempLink.setAttribute('download', panel.panel + '.pdf');
                document.body.appendChild(tempLink);
                tempLink.click();
                setTimeout(function(){
                    document.body.removeChild(tempLink);
                    window.URL.revokeObjectURL(url);
                }, 100);
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        }
    },

    render: function () {
        var onclick = null, glyph;
        switch (this.props.action) {
            case "modal":
                onclick = this.openModal;
                break;
            case "show":
                onclick = this.showTarget.bind(this, this.props.target);
                break;
            default:
                onclick = this.btn_action.bind(this, this.props.action);
        }
        if(this.props.hasOwnProperty('glyph')){
            glyph = <Bootstrap.Glyphicon glyph={this.props.glyph} />;
        }
        return (
            <Bootstrap.Button onClick={onclick}>
                {glyph}
                {this.props.name}
            </Bootstrap.Button>
        );
    }
});

var Heading = React.createClass({

    render: function () {
        return (
            <h3>
                {this.props.name}
            </h3>
        );
    }
});

var Paragraph = React.createClass({

    render: function () {
        return (
            <div>
                {this.props.name}
            </div>
        );
    }
});

var Frame = React.createClass({

    render: function () {
        return (
            <iframe key={this.props.name} src={this.props.src} className="iframe"></iframe>
        );
    }
});


module.exports = {
    "Filter": Filter,
    "Button": Button,
    "Heading": Heading,
    "Paragraph": Paragraph,
    "Frame": Frame
}
