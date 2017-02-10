var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var components = require('./basic_components');
var Reactable = require('reactable');

var Div = React.createClass({

    render: function () {
        var redux = {};
        var elements = this.props.elements.map(function(element) {
            element.key = element.name;
            var Component = components[element.type];
            redux[element.type] = connect(function(state){
                var newstate = {auth: state.auth};
                if(typeof element.reducers !== 'undefined'){
                    var r = element.reducers;
                    for (var i = 0; i < r.length; i++) {
                        newstate[r[i]] = state[r[i]];
                    }
                }
                return newstate;
            })(Component);
            var Redux = redux[element.type];
            return React.createElement(Redux, element);
        });
        var classes = this.props.class;
        if(typeof this.props.div !== 'undefined'){
            //TODO add other classes
            classes = this.props.div.show;
        }
        return (
            <div className={classes}>
                {elements}
            </div>
        );
    }
});

var Table = React.createClass({
    btn_clicked: function(id, evtKey){
        if(evtKey in this.props.modals){
            if("readonly" in this.props){
                var rows = this.props.table.tables[this.props.name].source.filter(function(row) {
                    if(row[this.props.id] == id){
                        return true;
                    }
                    return false;
                }.bind(this));
                var readonly = {};
                for(key in this.props.readonly){
                    readonly[this.props.readonly[key]] = rows[0][key];
                }
                this.props.dispatch({type: 'SET_READONLY', readonly: readonly});
            }
            var modal = this.props.modals[evtKey];
            modal.args = [id];
            this.props.dispatch({type: 'OPEN_MODAL', template: modal});
        }else{
            var data = {"instance_name": this.props.panel.instance, "action": evtKey, "args": [id]};
            var me = this;
            Network.post('/api/panels/action', this.props.auth.token, data).done(function(d) {
                var msg = d[me.props.panel.instance];
                if(msg){
                    me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                }else{
                    data.action = me.props.source;
                    data.args = []
                    me.props.dispatch({type: 'REFRESH_DATA', data: data});
                }
            });
        }
    },
    render: function () {
        var cols = Object.keys(this.props.table.tables[this.props.name].source[0]);
        var action_col = false;
        if(this.props.hasOwnProperty('actions')){
            var actions = this.props.actions.map(function(action) {
                var className = "";
                if(typeof action.class !== 'undefined'){
                    className = action.class;
                }
                return (
                    <Bootstrap.MenuItem key={action.name} eventKey={action.action} className={className}>{action.name}</Bootstrap.MenuItem>
                );
            });
            action_col = true;
        }
        var rows = this.props.table.tables[this.props.name].source.map(function(row) {
            var columns = cols.map(function(col) {
                return (
                    <Reactable.Td key={col} column={col}>
                        {row[col]}
                    </Reactable.Td>
                );
            });
            var key = row[this.props.id];
            if(action_col){
                action_col = <Reactable.Td column="action">
                    <Bootstrap.DropdownButton bsStyle='primary' title="Choose" onSelect = {this.btn_clicked.bind(this, key)}>
                        {actions}
                    </Bootstrap.DropdownButton>
                </Reactable.Td>
            }
            return (
                <Reactable.Tr key={key}>
                    {columns}
                    {action_col}
                </Reactable.Tr>
            )
        }.bind(this));
        return (
            <Reactable.Table className="table striped" columns={this.props.columns} itemsPerPage={5} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={cols} filterBy={this.props.table.filterBy} hideFilterInput >
                {rows}
            </Reactable.Table>
        );
    }
});

var Modal = React.createClass({

    getInitialState: function () {
        var content = this.props.modal.template.content, data = [];
        for(j=0; j<content.length; j++){
            if(content[j].type == "Form"){
                var elem = content[j].elements;
                for(i=0; i<elem.length; i++){
                    data[i] = elem[i].value;
                }
            }
        }
        var args = [];
        if("args" in this.props.modal.template){
            args = this.props.modal.template.args;
        }
        return {
            data: data,
            focus: "",
            args: args
        };
    },

    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    },

    action: function(action_name) {
        var data = {"instance_name": this.props.panel.instance, "action": action_name, "args": this.state.args.concat(this.state.data)};
        var me = this;
        Network.post("/api/panels/action", this.props.auth.token, data).done(function(d) {
            var msg = d[me.props.panel.instance];
            if(msg){
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
                me.props.dispatch({type: 'CLOSE_MODAL'});
            }else{
                me.props.dispatch({type: 'CLOSE_MODAL'});
            }
        });
    },

    form_changed: function(e) {
        var name = e.target.name;
        var val = e.target.value;
        var id = e.target.id;
        var data = this.state.data;
        if(e.target.type == "checkbox"){
            val = e.target.checked;
        }else{
            this.setState({focus: name});
        }
        data[id] = val;
        this.setState({data: data});
    },

    render: function () {
        var btns = this.props.modal.template.buttons.map(function(btn){
            if(btn.action == "cancel"){
                action = this.close;
            }else{
                action = this.action.bind(this, btn.action);
            }
            return <Bootstrap.Button key={btn.name} onClick={action} bsStyle = {btn.class}>{btn.name}</Bootstrap.Button>;
        }.bind(this));

        var redux = {};
        var elements = this.props.modal.template.content.map(function(element) {
            element.key = element.name;
            var Component = components[element.type];
            if(element.type == "Form"){
                element.data = this.state.data;
                element.form_changed = this.form_changed;
                element.focus = this.state.focus;
            }
            redux[element.type] = connect(function(state){
                var newstate = {auth: state.auth};
                if(typeof element.reducers !== 'undefined'){
                    var r = element.reducers;
                    for (var i = 0; i < r.length; i++) {
                        newstate[r[i]] = state[r[i]];
                    }
                }
                return newstate;
            })(Component);
            var Redux = redux[element.type];
            return React.createElement(Redux, element);
        }.bind(this));
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
            <Bootstrap.Modal.Header closeButton>
              <Bootstrap.Modal.Title>{this.props.modal.template.title}</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body>
                {elements}
            </Bootstrap.Modal.Body>

            <Bootstrap.Modal.Footer>
              {btns}
            </Bootstrap.Modal.Footer>

        </Bootstrap.Modal>
        );
    }
});

var Form = React.createClass({

    render: function () {
        var redux = {};

        var inputs = this.props.elements.map(function(element, index) {
            var type = element.type;
            if(type.charAt(0) === type.charAt(0).toLowerCase()){
                if(type == "checkbox"){
                    return ( <Bootstrap.Checkbox id={index} key={element.name} name={element.name} checked={this.props.data[index]} inline onChange={this.props.form_changed}>{element.label}</Bootstrap.Checkbox>);
                }
                if(type == "label"){
                    return ( <label id={index} key={element.name} name={element.name} className="block">{element.name}</label>);
                }
                if(type == "multi_checkbox"){
                    return ( <Bootstrap.Checkbox id={index} key={element.name} name={element.name} checked={this.props.data[index]} onChange={this.props.form_changed}>{element.label}</Bootstrap.Checkbox>);
                }
                if(type == "readonly_text"){
                    return ( <Bootstrap.FormControl id={index} key={element.name} type={type} name={element.name} value={this.props.form.readonly[element.name]} disabled /> );
                }
                if(type == "dropdown"){
                    return ( <Bootstrap.FormControl id={index} key={element.name} name={element.name} componentClass="select" placeholder={element.value[0]}>
                        {element.value.map(function(option, i) {
                            return <option key={i} value={option}>{option}</option>
                        })}
                    </Bootstrap.FormControl> );
                }
                return ( <Bootstrap.FormControl id={index} key={element.name} type={type} name={element.name} value={this.props.data[index]} placeholder={element.label} onChange={this.props.form_changed} autoFocus={element.name == this.props.focus} /> );
            }
            element.key = element.name;
            if(Object.keys(redux).indexOf(type) < 0){
                if(type == "Button" && element.action == "modal"){
                    element.modalTemplate = element.modal;
                }
                var Component = components[type];
                redux[type] = connect(function(state){
                    var newstate = {auth: state.auth};
                    if(typeof element.reducers !== 'undefined'){
                        var r = element.reducers;
                        for (var i = 0; i < r.length; i++) {
                            newstate[r[i]] = state[r[i]];
                        }
                    }
                    return newstate;
                })(Component);
            }
            var Redux = redux[type];
            return React.createElement(Redux, element);
        }.bind(this));

        return (
            <form className={this.props.class}>
                {inputs}
            </form>
        );
    }
});

components.Div = Div;
components.Table = Table;
components.Form = Form;
components.Modal = Modal;

module.exports = components;
