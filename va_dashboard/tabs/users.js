var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');
var Select = require('react-select-plus');

var UserGroupPanel = React.createClass({
    getInitialState: function () {
        return {
            funcs: [],
            groups: [],
            group_opt: [],
            loading: true,
        }
    },

    getCurrentFuncs: function () {
        var me = this;
        var n1 = Network.get('/api/panels/get_all_functions', this.props.auth.token)
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
        var n2 = Network.get('/api/panels/get_all_function_groups', this.props.auth.token)
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
        $.when( n1, n2 ).done(function ( resp1, resp2 ) {
            var groups = resp2.map(function(group) {
                return {value: group.func_name, label: group.func_name};
            });
            me.setState({funcs: resp1, groups: resp2, group_opt: groups, loading: false});
        }); 
    },

    componentDidMount: function () {
        this.getCurrentFuncs();
    },

    render: function () {
        var UserRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(Users);

        var loading = this.state.loading;
        const spinnerStyle = {
            display: loading ? "block": "none",
        };
        const blockStyle = {
            visibility: loading ? "hidden": "visible",
        };

        return (
            <div className="app-containter">
                <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x" aria-hidden="true"></i></span>
                <UserRedux funcs = {this.state.funcs} groups = {this.state.group_opt} style={blockStyle} />
            </div>
        )
    }
});


var Users = React.createClass({
    getInitialState: function () {
        return {
            users: [],
            modal_open: false,
            update: false,
            selected_user: {}
        }
    },

    getCurrentUsers: function () {
        var me = this;
        Network.get('/api/panels/users', this.props.auth.token)
        .done(function (data){
            me.setState({users: data});
        })
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    componentDidMount: function () {
        this.getCurrentUsers();
    },

    openModal: function() {
        this.setState({modal_open: true, update: false});
    },

    addUser: function(data) {
        var users = Object.assign([], this.state.users);
        data.functions = data.functions.map(function(f){
            return f.value;
        });
        users.push(data);
        this.setState({modal_open: false, users: users});
    },

    updateUser: function(index, data) {
        var users = Object.assign([], this.state.users);
        if(data.functions.length > 0 && typeof data.functions[0] === 'object'){
            data.functions = data.functions.map(function(f){
                return f.value;
            });
        }
        users[index] = data;
        this.setState({modal_open: false, users: users});
    },

    closeModal: function() {
        this.setState({modal_open: false});
    },

    btn_clicked: function(index, evtKey){
        var users = Object.assign([], this.state.users);
        var user = users[index];
        if(evtKey === "remove"){
            var data = {user: user.user}, me = this;
            Network.post('/api/panels/delete_user', this.props.auth.token, data).done(function(d) {
                users.splice(index, 1);
                me.setState({users: users});
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        }else{
            this.setState({modal_open: true, update: index, selected_user: user});
        }
    },

    render: function () {
        var user_rows = this.state.users.map(function(user, index) {
            var groups = user.groups.join(', ');
            var funcs = user.functions.join(', ');
            return (
                <Reactable.Tr key={user.user}>
                    <Reactable.Td column="Username">{user.user}</Reactable.Td>
                    <Reactable.Td column="Groups">{groups}</Reactable.Td>
                    <Reactable.Td column="Functions">{funcs}</Reactable.Td>
                    <Reactable.Td column="Actions">
                        <Bootstrap.DropdownButton bsStyle='primary' title="Choose" onSelect = {this.btn_clicked.bind(null, index)}>
                            <Bootstrap.MenuItem eventKey="remove">Remove</Bootstrap.MenuItem>
                            <Bootstrap.MenuItem eventKey="update">Update</Bootstrap.MenuItem>
                        </Bootstrap.DropdownButton>
                    </Reactable.Td>
                </Reactable.Tr>
            );
        }, this);

        var ModalRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(Modal);

        var modal;
        if(typeof this.state.update === "number"){
            modal = <ModalRedux type = {3} isOpen = {this.state.modal_open} update = {this.updateUser} index = {this.state.update} selected_user = {this.state.selected_user} close = {this.closeModal} funcs = {this.props.funcs} groups = {this.props.groups} />
        }else{
            modal = <ModalRedux type = {1} isOpen = {this.state.modal_open} add = {this.addUser} close = {this.closeModal} funcs = {this.props.funcs} groups = {this.props.groups} />
        }

        return ( 
            <div style={this.props.style} className="card">
                {modal}
                <div className="card-body">
                    <Reactable.Table className="table striped" columns={['Username', 'Groups', 'Functions', 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Username', 'Groups', 'Functions', 'Actions']} btnName="Add user" btnClick={this.openModal} title="Dashboard Users" filterClassName="form-control" filterPlaceholder="Filter">
                        {user_rows}
                    </Reactable.Table>
                </div>
            </div> 
        );
    }
});

var Groups = React.createClass({
    getInitialState: function () {
        return {
            groups: Object.assign([], this.props.groups),
            modal_open: false,
            update: false,
            selected_group: {}
        }
    },

    /*getCurrentGroups: function () {
        var me = this;
        Network.get('/api/panels/get_all_function_groups', this.props.auth.token)
        .done(function(data){
            me.setState({groups: data});
        })
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },*/

    openModal: function() {
        this.setState({modal_open: true, update: false});
    },

    addGroup: function(data) {
        var groups = Object.assign([], this.state.group);
        data.groups = data.groups.map(function(g){
            return g.value;
        });
        groups.push(data);
        this.setState({modal_open: false, groups: groups});
    },

    updateGroup: function(index, data) {
        var groups = Object.assign([], this.state.groups);
        if(data.functions.length > 0 && typeof data.functions[0] === 'object'){
            data.functions = data.functions.map(function(f){
                return f.value;
            });
        }
        groups[index] = data;
        this.setState({modal_open: false, groups: groups});
    },

    closeModal: function() {
        this.setState({modal_open: false});
    },

    btn_clicked: function(index, evtKey){
        var groups = Object.assign([], this.state.groups);
        var group = groups[index];
        if(evtKey === "remove"){
            var data = {group_name: group.func_name}, me = this;
            Network.post('/api/panels/delete_group', this.props.auth.token, data).done(function(d) {
                groups.splice(index, 1);
                me.setState({groups: groups});
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        }else{
            this.setState({modal_open: true, update: index, selected_group: group});
        }
    },

    render: function () {
        var group_rows = this.state.groups.map(function(group, index) {
            var funcs = group.functions.join(', ');
            return (
                <Reactable.Tr key={group.func_name}>
                    <Reactable.Td column="Group name">{group.func_name}</Reactable.Td>
                    <Reactable.Td column="Functions">{funcs}</Reactable.Td>
                    <Reactable.Td column="Actions">
                        <Bootstrap.DropdownButton bsStyle='primary' title="Choose" onSelect = {this.btn_clicked.bind(null, index)}>
                            <Bootstrap.MenuItem eventKey="remove">Remove</Bootstrap.MenuItem>
                            <Bootstrap.MenuItem eventKey="update">Update</Bootstrap.MenuItem>
                        </Bootstrap.DropdownButton>
                    </Reactable.Td>
                </Reactable.Tr>
            );
        }, this);

        var ModalRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert};
        })(Modal);

        var modal;
        if(typeof this.state.update === "number"){
            modal = <ModalRedux type = {4} isOpen = {this.state.modal_open} update = {this.updateGroup} index = {this.state.update} selected_group = {this.state.selected_group} close = {this.closeModal} funcs = {this.props.funcs} />
        }else{
            modal = <ModalRedux type = {2} isOpen = {this.state.modal_open} add = {this.addGroup} close = {this.closeModal} funcs = {this.props.funcs} />
        }

        return (
            <div style={this.props.style} className="card">
                {modal}
                <div className="card-body">
                    <Reactable.Table className="table striped" columns={['Group name', 'Functions', 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={true} filterable={['Group name', 'Functions', 'Actions']} btnName="Add group" btnClick={this.openModal} title="Dashboard Groups" filterClassName="form-control" filterPlaceholder="Filter">
                        {group_rows}
                    </Reactable.Table>
                </div>
            </div>
        );
    }
});


var Modal = React.createClass({
    getInitialState: function () {
        var data = {
            type: -1,
            value: null,
            group: null
        };
        var type = this.props.type;
        if(type === 3){
            var user = this.props.selected_user;
            data.value = user.functions;
            data.group = user.groups;
            data.user = user.user;
        }else if(type === 4){
            var group = this.props.selected_group;
            data.value = group.functions;
            data.group = group.func_name;
        }
        return data;
    },

    action: function(e) {
        var elements = ReactDOM.findDOMNode(this.refs.forma).elements;
        var data = {};
        for(i=0; i<elements.length; i++){
            data[elements[i].name] = elements[i].value;
        }
        console.log(data);
        var me = this, url = "/api/panels/create_user_group", type = this.props.type;
        delete data[""]
        if(type == 1 || type == 3){
            url =(type == 1) ? "/api/panels/create_user_with_group" : "/api/panels/update_user";
            var funcs = Object.assign([], this.state.value);
            if(funcs.length > 0 && typeof funcs[0] === 'object'){
                for(var i=0; i<funcs.length; i++){
                    funcs[i].group = funcs[i].group.label;
                }
            }
            data["functions"] = funcs;
            var groups = Object.assign([], this.state.group), g_arr = [];
            if(groups.length > 0){
                if(typeof groups[0] === 'object'){
                    for(var i=0; i<groups.length; i++){
                        g_arr.push(groups[i].value);
                    }
                }else{
                    g_arr = groups;
                }
            }
            data["groups"] = g_arr;
        }else{
            var funcs = Object.assign([], this.state.value);
            if(funcs.length > 0 && typeof funcs[0] === 'object'){
                for(var i=0; i<funcs.length; i++){
                    funcs[i].group = funcs[i].group.label;
                }
            }
            data["functions"] = funcs;
        }
        Network.post(url, this.props.auth.token, data).done(function(d) {
            type == 3 ? me.props.update(me.props.index, data) : me.props.add(data);
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    typeChange: function (evt) {
        this.setState({type: evt.target.value});
    },

    onChange(value) {
        this.setState({ value: value });
    },

    onChangeGroup(value) {
        this.setState({ group: value });
    },

    render: function () {
        var type = this.props.type;
        if(type === -1)
            return <div></div>;
        var title = "", form, btn_text = "", help_text = "";
        if(type === 1){
            var selectGroup = null, selectFunc = null, title="Add user", btn_text = "Add user", help_text = "Fill the form to add new user";
            if(this.state.type === "user"){
                selectGroup = <Select name="groups" options={this.props.groups} multi={true} placeholder="Select groups" value={this.state.group} onChange={this.onChangeGroup} />
                selectFunc = <Select name="functions" options={this.props.funcs} multi={true} placeholder="Select functions" value={this.state.value} onChange={this.onChange} />
            }
            form = (
                <div>
                    <Bootstrap.FormControl type='text' name="user" placeholder="Username" />
                    <Bootstrap.FormControl type='password' name="password" placeholder="Password" />
                    <select className="form-control" value={this.state.type} name="user_type" onChange={this.typeChange}>
                        <option value="-1" disabled>Select user type</option>
                        <option value="admin">Admin</option>
                        <option value="user">User</option>
                    </select>
                    {selectGroup}
                    {selectFunc}
                </div>
            );
        }else if(type === 2){
            var title="Add group", btn_text = "Add group", help_text = "Fill the form to add new group";
            form = (
                <div>
                    <Bootstrap.FormControl type='text' name="group_name" placeholder="Group name" />
                    <Select name="functions" options={this.props.funcs} multi={true} placeholder="Select functions" value={this.state.value} onChange={this.onChange} />
                </div>
            );
        }else if(type === 3){
            var title="Update user", btn_text = "Update user", help_text = "Fill the form to update the user";
            form = (
                <div>
                    <Bootstrap.FormControl type='text' name="user" value={this.state.user} disabled={true} />
                    <Bootstrap.FormControl type='password' name="password" placeholder="Password" />
                    <Select name="groups" options={this.props.groups} multi={true} placeholder="Select groups" value={this.state.group} onChange={this.onChangeGroup} />
                    <Select name="functions" options={this.props.funcs} multi={true} placeholder="Select functions" value={this.state.value} onChange={this.onChange} />
                </div>
            );
        }else{
            var title="Update group", btn_text = "Update group", help_text = "Fill the form to update the group";
            form = (
                <div>
                    <Bootstrap.FormControl type='text' name="group_name" value={this.state.group} />
                    <Select name="functions" options={this.props.funcs} multi={true} placeholder="Select functions" value={this.state.value} onChange={this.onChange} />
                </div>
            );
        }
        return (
            <Bootstrap.Modal show={this.props.isOpen} onHide={this.props.close}>
            <Bootstrap.Modal.Header closeButton>
              <Bootstrap.Modal.Title>{ title }</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body>
                <div className="left">
                    <Bootstrap.Form ref="forma">
                        { form }
                    </Bootstrap.Form>
                </div>
                <div className="right">
                    <h3>{help_text}</h3>
                    <div></div>
                </div>
            </Bootstrap.Modal.Body>

            <Bootstrap.Modal.Footer>
              <Bootstrap.Button onClick={this.props.close}>Cancel</Bootstrap.Button>
              <Bootstrap.Button onClick={this.action} bsStyle = "primary">{btn_text}</Bootstrap.Button>
            </Bootstrap.Modal.Footer>

        </Bootstrap.Modal>
        );
    }
});

UserGroupPanel = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(UserGroupPanel);

var GroupRedux = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Groups);


module.exports = {
    Panel: UserGroupPanel,
    Group: GroupRedux
};
