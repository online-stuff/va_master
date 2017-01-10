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
            if(element.type == "Table"){
                redux[element.type] = connect(function(state){
                    return {auth: state.auth, table: state.table};
                })(Component);
            }else{
                redux[element.type] = connect(function(state){
                    return {auth: state.auth};
                })(Component);
            }
            var Redux = redux[element.type];
            return React.createElement(Redux, element);
        });
        return (
            <div className={this.props.class}>
                {elements}
            </div>
        );
    }
});

var Table = React.createClass({
    btn_clicked: function(id, evtKey){
        console.log(id);
        console.log(evtKey);
        var arr = evtKey.split(".");
        // var data = {id: id, action: arr[1]};
        // Network.post('/api/' + arr[0], this.props.auth.token, data).done(function(d) {
        //     console.log(d);
        // });
    },
    render: function () {
        var cols = Object.keys(this.props.source[0]);
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
        var rows = this.props.source.map(function(row) {
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
        var content = this.props.content, data = {};
        for(j=0; j<content.length; j++){
            if(content[j].type == "Form"){
                var elem = content[j].elements;
                for(i=0; i<elem.length; i++){
                    data[elem[i].name] = elem[i].value;
                }
            }
        }
        console.log("initial state in modal");
        console.log(data);
        // this.props.dispatch({type: 'UPDATE_FORM', data: data});
        return {
            data: data,
            focus: ""
        };
    },

    open: function() {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },

    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    },

    action: function(action_name) {
        console.log(action_name);
        console.log(this.state.data);
        // this.props.dispatch({type: 'SEND_FORM', url: action_name});
        // console.log(this.props.form.data);
        //Network.post();
    },

    form_changed: function(e) {
        var name = e.target.name;
        var val = e.target.value;
        var data = this.state.data;
        if(e.target.type == "checkbox"){
            val = e.target.checked;
        }else{
            this.setState({focus: name});
        }
        data[name] = val;
        this.setState({data: data});
        console.log("in form change");
        console.log(data);
        // this.props.dispatch({type: 'UPDATE_FORM', data: data});
    },

    render: function () {
        var btns = this.props.buttons.map(function(btn){
            if(btn.action == "cancel"){
                action = this.close;
            }else{
                action = this.action.bind(this, btn.action);
            }
            return <Bootstrap.Button key={btn.name} onClick={action} bsStyle = {btn.class}>{btn.name}</Bootstrap.Button>;
        }.bind(this));

        var redux = {};
        var elements = this.props.content.map(function(element) {
            element.key = element.name;
            var Component = components[element.type];
            if(element.type == "Form"){
                element.data = this.state.data;
                element.form_changed = this.form_changed;
                element.focus = this.state.focus;
            }
            redux[element.type] = connect(function(state){
                return {auth: state.auth};
            })(Component);
            var Redux = redux[element.type];
            return React.createElement(Redux, element);
        }.bind(this));
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
            <Bootstrap.Modal.Header closeButton>
              <Bootstrap.Modal.Title>{this.props.title}</Bootstrap.Modal.Title>
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
    // getInitialState: function () {
    //     var data = {};
    //     if(this.props.form_type == "basic"){
    //         var elem = this.props.elements;
    //         for(i=0; i<elem.length; i++){
    //             data[elem[i].name] = elem[i].value;
    //         }
    //     }
    //     // if(this.props.form_type == "basic"){
    //     //     data = this.props.data;
    //     // }
    //     console.log("initial state");
    //     console.log(data);
    //     return {
    //         data: data
    //     };
    // },

    // form_changed: function(e) {
    //     var name = e.target.name;
    //     var val = e.target.value;
    //     var data = this.state.data;
    //     if(e.target.type == "checkbox"){
    //         val = e.target.checked;
    //     }
    //     data[name] = val;
    //     this.setState({data: data});
    //     console.log("in change");
    //     console.log(data);
    //     // this.props.dispatch({type: 'UPDATE_FORM', data: data});
    // },

    sendForm: function () {
        var data = this.state.data;
        console.log(data);
        // this.props.dispatch({type: 'SEND_FORM', url: data});
        // Network.post('/api/', this.props.auth.token, data);
    },

    render: function () {
        var redux = {};
        var ModalRedux = connect(function(state){
            return {auth: state.auth, modal: state.modal};
        })(Modal);

        var modal = false, modalElem = null;

        var inputs = this.props.elements.map(function(element) {
            var type = element.type;
            if(type.charAt(0) === type.charAt(0).toLowerCase()){
                if(type == "checkbox"){
                    return ( <Bootstrap.Checkbox key={element.name} name={element.name} checked={this.props.data[element.name]} inline onChange={this.props.form_changed}>{element.label}</Bootstrap.Checkbox>);
                }
                return ( <Bootstrap.FormControl key={element.name} type={type} name={element.name} value={this.props.data[element.name]} placeholder={element.label} onChange={this.props.form_changed} autoFocus={element.name == this.props.focus} /> );
            }
            element.key = element.name;
            if(Object.keys(redux).indexOf(type) < 0){
                if(type == "Button" && element.action == "modal"){
                    modal = true;
                    modalElem = element.modal;
                }
                var Component = components[type];
                redux[type] = connect(function(state){
                    if(type == "Filter"){
                        return {auth: state.auth, table: state.table};
                    }
                    return {auth: state.auth};
                })(Component);
            }
            var Redux = redux[type];
            return React.createElement(Redux, element);
        }.bind(this));

        return (
            <Bootstrap.Form className={this.props.class}>
                {inputs}
                {modal && React.createElement(ModalRedux, modalElem) }
            </Bootstrap.Form>
        );
    }
});

components.Div = Div;
components.Table = Table;
components.Form = Form;
components.Modal = Modal;

module.exports = components;
