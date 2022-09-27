import dearpygui.dearpygui as dpg

dpg.create_context()

def change_tab(sender, app_data):
    #if the sender is the tag 100 ( Button 1 ) we set the value of the test_tab_bar to the test_tab_2
    #if the sender isn't the tag 100 ( Button 1) we set the value of the test_tab_bar to the test_tab_1
    if sender == 100:
        dpg.set_value("test_tab_bar", "test_tab_2")
    else:
        dpg.set_value("test_tab_bar", "test_tab_1")


with dpg.window(label="Window", tag="window"):
    #creating the tab bar
    with dpg.tab_bar(tag="test_tab_bar") as tb:
        #creating a tab with the tag test_tab_1
        with dpg.tab(label="tab 1", tag="test_tab_1"):
            #creating a button that executes the callback change_tab with the tag 100
            dpg.add_button(label="activate tab 2", callback=change_tab, tag=100)
        #creating a tab with the tag test_tab_2
        with dpg.tab(label="tab 2", tag="test_tab_2"):
            #creating a button that executes the callback change_tab with the tag 200
            dpg.add_button(label="activate tab 1", tag=200, callback=change_tab,)

dpg.create_viewport(title="Tab_bar switch")
dpg.set_primary_window("window", True)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()