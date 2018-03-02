import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import { callPanelAction, download } from './util';

class Filter extends Component {

    componentDidMount(){
		var elem = this.refs[this.props.name], pos = elem.value.length;
		elem.focus();
		elem.setSelectionRange(pos, pos);
    }

    filter(e) {
        this.props.dispatch({type: 'FILTER', filterBy: e.target.value});
    }

    render () {
        let { name, filter } = this.props;
        return (
            <Bootstrap.InputGroup>
                <input
                    id={name}
                    type="text"
                    className="form-control"
                    placeholder="Filter"
                    value={filter.filterBy}
                    onChange={(e) => this.filter(e)}
                    ref={name}
                />
                <Bootstrap.InputGroup.Addon>
                  <Bootstrap.Glyphicon glyph="search" />
                </Bootstrap.InputGroup.Addon>
            </Bootstrap.InputGroup>
        );
    }
}

class Button extends Component {

    openModal () {
        var modal = this.props.modalTemplate;
        this.props.dispatch({type: 'OPEN_MODAL', template: modal});
    }

    showTarget (target) {
        this.props.dispatch({type: 'TOGGLE'});
    }

    btn_action (action) {
        if("tblName" in this.props){
            var panel = this.props.panel, export_type = this.props.export_type;
            var filterVal = document.getElementById('reactableFilter').value;
            var data = {server_name: panel.server, panel: panel.panel, args: panel.args, table_name: this.props.tblName, filter_field: filterVal, export_type: export_type};
            download('/api/panels/export_table', this.props.auth.token, data, `${panel.panel}.${export_type}`, (msg) => {
                this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        }else if('action' in this.props){
			//let data = { action: this.props.action };
            //if('data' in this.props) data = Object.assign(data, this.props.data);
            let data = 'data' in this.props ? this.props.data : {};
            callPanelAction(this.props.auth.token, data, (msg) => {
                this.props.dispatch({type: 'SHOW_ALERT', msg});
            }, (msg) => {
                this.props.dispatch({type: 'SHOW_ALERT', msg});
            });
        }
    }

    render () {
        var onclick = null, glyph;
        switch (this.props.action) {
            case "modal":
                onclick = this.openModal.bind(this);
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
}

const Heading = (props) => {
    return (
        <h3>
            {props.name}
        </h3>
    );
}

const Paragraph = (props) => {
    return (
        <div>
            {props.name}
        </div>
    );
}

const Frame = (props) => {
    return (
        <iframe key={props.name} src={props.src} className="iframe"></iframe>
    );
}


module.exports = {
    "Filter": Filter,
    "Button": Button,
    "Heading": Heading,
    "Paragraph": Paragraph,
    "Frame": Frame
}
