# PyQT5 Interface libaries
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow

# Essential Libraries
import matplotlib.pyplot as plt
import numpy as np
import time
import sys
import cv2

# Decorator
from functools import wraps

# Partition Operations
from Clustering_Operations import Clustering_Operations
from Heuristic_Operatipns import Heuristic_Operations

# Get_Data_Dialog
from Get_Data_Dialog import Get_Data_Dialog


# Define the decorator
def progress_bar_decorator(time_delay):
    """
    @brief Decorator to add a progress bar to the status bar.
    @param time_delay The delay for the progress bar.
    @return The wrapper function.
    @details This decorator adds a progress bar to the status bar and updates it based on the time delay.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Temporary progress bar generation
            layout = QtWidgets.QVBoxLayout()
            progress_bar = QtWidgets.QProgressBar()
            progress_bar.setRange(0, 100)
            progress_bar.setFixedHeight(15)
            layout.addWidget(progress_bar)
            
            # Add progress bar to the status bar
            self.statusBar().addPermanentWidget(progress_bar)
            
            for i in range(101):
                time.sleep(time_delay / 100)
                progress_bar.setValue(i)
            self.statusBar().removeWidget(progress_bar)
            
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


# Clustering_Operations requires Point_Matrix class from Data.py from init
class UI_Interface(QMainWindow, Clustering_Operations, Heuristic_Operations):
    """
    @brief Main user interface class for clustering and heuristic operations.
    @details This class handles the UI interactions, connects buttons to functions, 
             and manages history elements for the solutions.
    """
    
    def __init__(self, template_path):
        """
        @brief Constructor to initialize the UI interface.
        @param template_path Path to the UI template file.
        """
        super(UI_Interface, self).__init__( data = None )

        uic.loadUi(template_path, self)
        self.show()
        
        # History elements initialization
        self.initial_solution_png_hist = []; self.initial_solution_hist_index = 0
        self.final_solution_png_hist = []; self.final_solution_hist_index = 0
        self.information_panel_hist = []; self.information_panel_hist_index = 0
        self.results_panel_hist = []; self.results_panel_hist_index = 0
        self.nodes_hist = []; self.nodes_hist_index = 0
        self.hubs_hist = []; self.hubs_hist_index = 0

        # Initialize the UI
        self.init_ui()


    ###################### UI Operations ######################

    def init_ui(self):
        """
        @brief Initializes the UI components and connects buttons to functions.
        """
        # Hide the full menu widget
        self.full_menu_widget.setVisible(False)

        # Connect buttons to functions
        self.open_data.clicked.connect(self.load_data_button)
        self.menu_open_data.triggered.connect(self.open_data.click)
        
        # Connect the manual run button to the function
        self.manual_run.clicked.connect(self.manual_run_clicked)

        # Connect the menu buttons to the functions
        self.menu_clear_initial_solution.triggered.connect(self.clear_initial_solution)
        self.menu_clear_final_solution.triggered.connect(self.clear_final_solution)
        
        # Connect the exit buttons to the function
        self.exit_button.clicked.connect(self.exit_app)
        self.exit_menu.triggered.connect(self.exit_button.click)

        # Initialize side menu buttons
        self.init_side_buttons()

        # Side menu buttons
        self.side_menu_buttons = [ self.initial_solution_side, self.final_solution_side, self.clustering_side, self.heuristics_side ]
        [ button.clicked.connect(self.sidebar_button_clicked) for button in self.side_menu_buttons ]

        # Initialize the data
        self.change_buttons_state("default", True)

    # Get buttons from the UI
    def get_buttons(self):
        """
        @brief Retrieves all buttons from the UI.
        @return List of buttons (QPushButton and QMenu objects).
        """
        # Temporary buttons array
        buttons = []

        # Get all QPushButton objects
        for button in self.findChildren(QtWidgets.QPushButton):
            buttons.append(button)
        # Get all QMenu objects
        for button in self.findChildren(QtWidgets.QMenu):
            buttons.append(button)

        # Manually added buttons
        buttons.append(self.menu_initial_save)
        buttons.append(self.menu_final_save)

        return buttons
    
    def change_buttons_state(self, state = "default", visible = True):
        """
        @brief Changes the enabled state of buttons.
        @param state The state to set the buttons to. Can be "full", "source_opened" or "default".
        @param visible Boolean indicating whether the buttons should be visible or not.
        """

        if state == "source_opened":
            edit_buttons = [
                self.final_solution_side, 
                self.menu_initial_save, self.menu_final_save,
                self.menu_initial_export_as, self.menu_final_export_as,
                self.menu_clear_final_solution
            ]
        elif state == "default":
            edit_buttons = [
                self.open_data, self.exit_menu, self.exit_button, self.menu_open_data, self.menu_file,
                self.findChild(QtWidgets.QPushButton, "source_open"), 
            ]
        elif state == "full":
            edit_buttons = []
            
        for button in self.get_buttons():
            if button in edit_buttons:
                button.setEnabled(visible)
            else:
                button.setEnabled(not visible)

    ###################### Manual Operations ######################

    def manual_run_clicked(self):
        """
        @brief Executes the manual clustering operation based on user input.
        """
        # QTextEdit 
        hubs = self.manual_hubs.toPlainText()
        nodes = self.manual_nodes.toPlainText()

        # Clear the information and results panels before the operation
        self.clear_data_information_panel()
        self.clear_data_results_panel()

        # Get the arguments for the clustering operation
        hubs = [ int(hub) for hub in hubs.split(" ") ]

        # Progress bar for the clustering operation
        self.constant_cluster_hubs_calculation(hubs)

        # Print the results and plot the final solution
        if self.plot_final_solution() == False:
            self.add_data_infromation_panel("There is no cluster information to display.")
            return
        
        self.print_cluster_information()

        self.update_history(self.monitor_information_panel.toPlainText(), self.information_panel_hist, self.information_panel_hist_index)
        self.update_history(self.monitor_results.toPlainText(), self.results_panel_hist, self.results_panel_hist_index)

        self.update_history(self.manual_hubs.toPlainText(), self.hubs_hist, self.hubs_hist_index)
        self.update_history(self.manual_nodes.toPlainText(), self.nodes_hist, self.nodes_hist_index)
        
    
    ##############################################################

    ###################### Monitor Operations ######################


    # Display functions
    @progress_bar_decorator(0.4)
    def plot_initial_solution(self):
        """
        @brief Plots the initial solution on the monitor.
        """
        
        # get plot
        initial_solution_data = self.get_data()
        label_size = self.monitor_initial_solution.width(), self.monitor_initial_solution.height()
        
        # 2D plot
        fig, ax = self.init_figure()

        for point in initial_solution_data:
            ax.scatter(point.get_coordinates()[0], point.get_coordinates()[1], c='black')
            ax.text(point.get_coordinates()[0], point.get_coordinates()[1], str(point.get_id()), fontsize=12)
        
        # Convert plot to pixmap
        pixmap = self.plot_to_pixmap(fig, label_size)
        self.monitor_initial_solution.setPixmap(pixmap)
        plt.close(fig)

        # Append to initial solution image history
        self.update_history(pixmap, self.initial_solution_png_hist, self.initial_solution_hist_index)


    # Plot final solution
    @progress_bar_decorator(0.4)
    def plot_final_solution(self):
        """
        @brief Plots the final solution on the monitor.
        @return False if there is no cluster information to display, otherwise True.
        """
        
        # Get label size
        label_size = self.monitor_final_solution.width(), self.monitor_final_solution.height()
        
        # Get output data
        try:
            cluster_centers = self.calculate_cluster_centers()
            center_nodes = [ point.get_coordinates() for point in self.calculate_center_nodes() ]
        except:
            return False

        # Generate 2D Plot 
        fig, ax = self.init_figure()
        color_list = [ 'red', 'green', 'yellow', 'purple', 'orange', 'pink', 'cyan', 'magenta', 'brown', 'gray' ]
        
        for point in self.get_data():
            if point.get_coordinates() in center_nodes:
                ax.scatter(point.get_coordinates()[0], point.get_coordinates()[1], c='blue')
                ax.text(point.get_coordinates()[0], point.get_coordinates()[1], str(point.get_id()), fontsize=12)
            else:
                ax.scatter(point.get_coordinates()[0], point.get_coordinates()[1], c=color_list[point.get_cluster_id()])
                ax.text(point.get_coordinates()[0], point.get_coordinates()[1], str(point.get_id()), fontsize=12)
        
        for cluster_pos in cluster_centers:
            ax.scatter(cluster_pos[0], cluster_pos[1], c='blue', s=100, marker='x')
        

        # Convert plot to pixmap
        pixmap = self.plot_to_pixmap(fig, label_size)
        self.monitor_final_solution.setPixmap(pixmap)
        plt.close(fig)

        # Append to final solution image history
        self.update_history(pixmap, self.final_solution_png_hist, self.final_solution_hist_index)

        # Button state change
        self.change_buttons_state("full", False)

    # Clear functions
    def clear_final_solution(self):
        """
        @brief Clears the final solution display.
        """
        self.monitor_final_solution.clear()
        self.change_buttons_state("source_opened", False)

    def clear_initial_solution(self):
        """
        @brief Clears both initial and final solution displays.
        """
        self.monitor_initial_solution.clear()
        self.monitor_final_solution.clear()
        self.change_buttons_state("default", True)

    def update_history(self, pixmap, history, index):
        """
        @brief Updates the history of solution images.
        @param pixmap The pixmap to add to history.
        @param history The history list to update.
        @param index The current index in the history.
        """

        if index == 0:
            history.insert(0, pixmap)
        else:
            history = history[index:]
            history.insert(0, pixmap)
            index = 0

    # Cluster information print
    def print_cluster_information(self, ret=None):
        """
        @brief Prints detailed cluster information to the results panel.
        @param ret Optional parameter to include additional information in the output.
        """

        # Gather information
        cluster_centers_label = self.calculate_cluster_centers()
        rounded_cluster_centers = [ (round(center[0], 2), round(center[1], 2)) for center in cluster_centers_label ]
        cluster_items = self.get_cluster_items() 
        pair_objectives, max_pair_objective = self.calculate_pair_objectives()

        # Results panel functions
        self.add_data_results_panel("Clustering labels: " + str(self.get_cluster_vector()))
        self.add_data_results_panel("\nCluster centers: " + str(rounded_cluster_centers).replace("  ", "").replace("\n", " ")+"\n")

        self.add_data_results_panel("There are " + str(len(cluster_items)) + " clusters:")
        for cluster_id, cluster_items in cluster_items.items():
            self.add_data_results_panel("\nCluster " + str(cluster_id) + " items: " + 
                str( [ item.get_id() for item in cluster_items ] ))
            
        self.add_data_results_panel("\n\nCluster Center Nodes: " + str([ point.get_id() for point in self.calculate_center_nodes() ]))

        self.add_data_results_panel("\n\nFarthest Hub Distances: \n" + str(self.calculate_distances_from_center()))
        self.add_data_results_panel("\n\nAll Possible Pairs: \n" + str([ (point_tuple[0].get_id(), point_tuple[1].get_id())
                                                                            for point_tuple in self.calculate_all_possible_pairs() ]))
        self.add_data_results_panel("\n\nPair Objectives: \n" + str(pair_objectives))
        self.add_data_results_panel("\n\nMax Pair Objective: \n" + str(max_pair_objective))

        if ret:
            str_dict = ", ".join( [ str(key) + ": " + str(value) for key, value in ret.items() ] )
            
            # has ret key "auto"
            if "auto" in ret.keys() and ret["auto"] == True:
                self.add_data_infromation_panel("The clustering operation could not be successful with the given parameters!\nAuto parameters are used.")

            self.add_data_infromation_panel("\n\nParameters:\n" + str_dict)

    ##############################################################

    # Panel functions                                                                                

    def add_data_infromation_panel(self, data):
        """
        @brief Adds text to the information panel.
        @param text The text to add to the information panel.
        """
        old_text = self.monitor_information_panel.toPlainText()
        self.monitor_information_panel.setText(
            old_text + data
        )

    def add_data_results_panel(self, data):
        """
        @brief Adds text to the results panel.
        @param text The text to add to the results panel.
        """
        old_text = self.monitor_results.toPlainText()
        self.monitor_results.setText(
            old_text + "\n" + data
        )
    
    def clear_data_results_panel(self):
        """
        @brief Clears the results panel.
        """
        self.monitor_results.clear()

    def clear_data_information_panel(self):
        """
        @brief Clears the information panel.
        """
        self.monitor_information_panel.clear()


    ###################################################################

    ###################### Clustering Operations ######################

    def clustering_button_clicked(self):
        """
        @brief Handles the event when a clustering-related button is clicked.
        """

        # Get the sender
        sender = self.sender()

        # Clear the information and results panels before the operation
        self.clear_data_information_panel()
        self.clear_data_results_panel()

        sender_name = sender.text().replace("menu_", "")

        # Get the arguments for the clustering operation, respect to the sender
        if sender_name == 'K-Means':
            dialog = Get_Data_Dialog(
                ["Number of clusters: ", ["Init: ", "k-means++", "random"], "Max iterations: ", ["Algorithm: ", "auto", "full", "elkan"]],
                ["3", "", "300", ""]
                )
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                data = dialog.get_input()
                
                args_dict = { 
                    "n_clusters": int(data[0]) if data[0] != '' else 3, # Default value is 3
                    "init": data[1],
                    "max_iter": int(data[2]) if data[2] != '' else 300, # Default value is 300
                    "algorithm": data[3]
                }
            else:
                return

        elif sender_name == 'Affinity Propagation':
            dialog = Get_Data_Dialog(
                ["Damping: ", "Max iterations: ", "Convergence iteration: "],
                ["0.5", "200", "15"]
            )
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                data = dialog.get_input()
                
                args_dict = { 
                    "damping": float(data[0]) if data[0] != '' else 0.5, # Default value is 0.5
                    "max_iter": int(data[1]) if data[1] != '' else 200, # Default value is 200
                    "convergence_iter": int(data[2]) if data[2] != '' else 15, # Default value is 15
                }
            else:
                return

        elif sender_name == 'Mean Shift':
            dialog = Get_Data_Dialog(
                ["Bandwidth: ", "Max iterations: "],
                ["250", "300"]
            )
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                data = dialog.get_input()
                
                args_dict = { 
                    "bandwidth": float(data[0]) if data[0] != '' else 250, # Default value is None
                    "max_iter": int(data[1]) if data[1] != '' else 300, # Default value is 300
                }
            else:
                return

        elif sender_name == 'Spectral Clustering':
            dialog = Get_Data_Dialog(
                ["Number of clusters: ", ["Assign labels: ", "kmeans", "discretize"], ["Eigen solver: ", "arpack", "lobpcg", "amg"], "Random state: "],
                ["3", "", "", "None"] 
            )
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                data = dialog.get_input()
                
                args_dict = { 
                    "n_clusters": int(data[0]) if data[0] != '' else 3, # Default value is 3
                    "assign_labels": data[1],
                    "eigen_solver": data[2],
                    "random_state": int(data[3]) if data[3] != '' else None, # Default value is None
                }
            else:
                return

        elif sender_name == 'Hierarchical Clustering':
            dialog = Get_Data_Dialog(
                ["Number of clusters: ", ["Linkage: ", "ward", "complete", "average", "single"], "Distance threshold: "],
                ["2", "", "None"]
            )
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                data = dialog.get_input()
                
                args_dict = { 
                    "n_clusters": int(data[0]) if data[0] != '' else 2, # Default value is 2
                    "linkage": data[1],
                    "distance_threshold": float(data[2]) if data[2] != '' else None, # Default value is None
                }
            else:
                return

        elif sender_name == 'DBSCAN':
            dialog = Get_Data_Dialog(
                ["Epsilon: ", "Min samples: ", ["Metric: ", "euclidean", "manhattan", "chebyshev", "minkowski"],"N_Clusters(Used for auto mode): "],
                ["0.5", "5", "", "3"]
            )
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                data = dialog.get_input()
                
                args_dict = { 
                    "eps": float(data[0]) if data[0] != '' else 0.5, # Default value is 0.5
                    "min_samples": int(data[1]) if data[1] != '' else 5, # Default value is 5
                    "metric": data[2] if data[2] != '' else 'euclidean', # Default value is 'euclidean'
                }
            else:
                return

        # Run the clustering operation
        ret = self.method_handler_clustering(sender_name, args_dict)
        
        # Print the results and plot the final solution
        if self.plot_final_solution() == False:
            self.add_data_infromation_panel("There is no cluster information to display.")
            return
        
        # Print arg dict to information panel
        self.add_data_infromation_panel("\n\nParameters that collected from the user:\n")
        for key, value in args_dict.items():
            self.add_data_infromation_panel(key + ": " + str(value) + ", " )
        self.add_data_infromation_panel("\n\n")


        self.print_cluster_information(ret)

        self.update_history(self.monitor_information_panel.toPlainText(), self.information_panel_hist, self.information_panel_hist_index)
        self.update_history(self.monitor_results.toPlainText(), self.results_panel_hist, self.results_panel_hist_index)

    ###################################################################

    ###################### Heuristics Operations ######################

    def heuristics_button_clicked(self):
        """
        @brief Handles the event when a heuristics-related button is clicked.
        """

        sender_name = self.sender().text().replace("menu_", "")

        # Clear the information and results panels before the operation
        self.clear_data_information_panel()
        self.clear_data_results_panel()

        if sender_name == 'Hill Climbing':
            dialog = Get_Data_Dialog(
                ["Max iterations: ", "N_clusters: ", "Swap nodes chance: ", "Reallocate node chance: "],
                ["1000", "3", "0.1", "0.1"]
            )
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                data = dialog.get_input()
                
                args_dict = { 
                    "max_iterations": int(data[0]) if data[0] != '' else 1000, # Default value is 1000
                    "n_clusters": int(data[1]) if data[1] != '' else 3, # Default value is 3
                    "swap_nodes_chance": float(data[2]) if data[2] != '' else 0.1, # Default value is 0.1
                    "reallocate_node_chance": float(data[3]) if data[3] != '' else 0.1, # Default value is 0.1
                }
            else:
                return
            
        elif sender_name == 'Simulated Annealing':
            dialog = Get_Data_Dialog(
                ["Max iterations: ", "Initial temperature: ", "Cooling rate: ", "N_clusters: ", "Swap nodes chance: ", "Reallocate node chance: "],
                ["1000", "100.0", "0.99", "3", "0.1", "0.1"]
            )
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                data = dialog.get_input()
                
                args_dict = { 
                    "max_iterations": int(data[0]) if data[0] != '' else 1000, # Default value is 1000
                    "initial_temperature": float(data[1]) if data[1] != '' else 100.0, # Default value is 100.0
                    "cooling_rate": float(data[2]) if data[2] != '' else 0.99, # Default value is 0.99
                    "n_clusters": int(data[3]) if data[3] != '' else 3, # Default value is 3
                    "swap_nodes_chance": float(data[4]) if data[4] != '' else 0.1, # Default value is 0.1
                    "reallocate_node_chance": float(data[5]) if data[5] != '' else 0.1, # Default value is 0.1
                }
            else:
                return


        # Run the clustering operation
        ret = self.method_handler_heuristics(sender_name, args_dict)
        
        # Print the results and plot the final solution
        if self.plot_final_solution() == False:
            self.add_data_infromation_panel("There is no cluster information to display.")
            return

        # Print arg dict to information panel
        self.add_data_infromation_panel("\n\nParameters that collected from the user:\n")
        for key, value in args_dict.items():
            self.add_data_infromation_panel(key + ": " + str(value) + ", " )
        self.add_data_infromation_panel("\n\n")


        self.print_cluster_information(ret)

        self.update_history(self.monitor_information_panel.toPlainText(), self.information_panel_hist, self.information_panel_hist_index)
        self.update_history(self.monitor_results.toPlainText(), self.results_panel_hist, self.results_panel_hist_index)

    ##############################################################

    ###################### Side Bar ##############################
    
    def sidebar_button_clicked(self):
        """
        @brief Handles the event when a sidebar button is clicked.
        """

        # Get the sender
        sender = self.sender()

        # Hide the full menu widget if the sender is different
        if not hasattr(self, 'hold_sender') or self.hold_sender != sender or not self.full_menu_widget.isVisible():
            self.full_menu_widget.setVisible(True)
        else:
            self.full_menu_widget.setVisible(False)

        # Edit the full menu buttons and hold the sender
        self.change_side_buttons_visibility(sender)    
        self.hold_sender = sender

    def init_side_buttons(self):
        """
        @brief Initializes the sidebar buttons.
        """

        buttons = [
            # Initial Solution
            { 'name': 'Save As', 'object_name': 'initial_save_as', 'function': self.initial_solution_button_clicked },
            { 'name': 'Save', 'object_name': 'initial_save', 'function': self.initial_solution_button_clicked },
            { 'name': 'Export As', 'object_name': 'initial_export_as', 'function': self.initial_solution_button_clicked },
            { 'name': 'Undo', 'object_name': 'initial_undo', 'function': self.initial_solution_button_clicked },
            { 'name': 'Redo', 'object_name': 'initial_redo', 'function': self.initial_solution_button_clicked },

            # Final Solution
            { 'name': 'Save As', 'object_name': 'final_save_as', 'function': self.final_solution_button_clicked },
            { 'name': 'Save', 'object_name': 'final_save', 'function': self.final_solution_button_clicked },
            { 'name': 'Export As', 'object_name': 'final_export_as', 'function': self.final_solution_button_clicked },
            { 'name': 'Undo', 'object_name': 'final_undo', 'function': self.final_solution_button_clicked },
            { 'name': 'Redo', 'object_name': 'final_redo', 'function': self.final_solution_button_clicked },
            
            # Clustering
            { 'name': 'K-Means', 'object_name': 'clustering_kmeans', 'function': self.clustering_button_clicked },
            { 'name': 'Affinity Propagation', 'object_name': 'clustering_affinity_propagation', 'function': self.clustering_button_clicked },
            { 'name': 'Mean Shift', 'object_name': 'clustering_mean_shift', 'function': self.clustering_button_clicked },
            { 'name': 'Spectral Clustering', 'object_name': 'clustering_spectral_clustering', 'function': self.clustering_button_clicked },
            { 'name': 'Hierarchical Clustering', 'object_name': 'clustering_hierarchical_clustering', 'function': self.clustering_button_clicked },
            { 'name': 'DBSCAN', 'object_name': 'clustering_dbscan', 'function': self.clustering_button_clicked },
            
            # Heuristics
            { 'name': 'Hill Climbing', 'object_name': 'heuristics_hill_climbing', 'function': self.heuristics_button_clicked },
            { 'name': 'Simulated Annealing', 'object_name': 'heuristics_simulated_annealing', 'function': self.heuristics_button_clicked }
        ]

        # Generate buttons
        for button_dict in buttons:
            button = QtWidgets.QPushButton(button_dict['name'])
            button.setObjectName(button_dict['object_name'])
            button.clicked.connect(button_dict['function'])
            self.toolbox_layout.addWidget(button)

            # Assign the menu button to the button
            menu_button = self.findChild(QtWidgets.QAction, 'menu_' + button_dict['object_name'])
            if menu_button:
                menu_button.triggered.connect(button.click)

    def change_side_buttons_visibility(self, sender):
        """
        @brief Changes the visibility of sidebar buttons based on the sender.
        @param sender: The sender object triggering the method.
        """
        
        # Hide all buttons of self.toolbox_layout
        for i in range(self.toolbox_layout.count()):
            self.toolbox_layout.itemAt(i).widget().setVisible(False)
            
        # Respect to the sender, show the buttons
        if sender == self.initial_solution_side:
            button_object_names = [ 'initial_save_as', 'initial_save', 'initial_export_as', 'initial_undo', 'initial_redo' ]
        elif sender == self.final_solution_side:
            button_object_names = [ 'final_save_as', 'final_save', 'final_export_as', 'final_undo', 'final_redo' ]
        elif sender == self.clustering_side:
            button_object_names = [ 'clustering_kmeans', 'clustering_affinity_propagation', 'clustering_mean_shift', 'clustering_spectral_clustering', 'clustering_hierarchical_clustering', 'clustering_dbscan' ]
        elif sender == self.heuristics_side:
            button_object_names = [ 'heuristics_hill_climbing', 'heuristics_simulated_annealing' ]

        for button_object_name in button_object_names:
            button = self.findChild(QtWidgets.QPushButton, button_object_name)
            button.setVisible(True)
        

    ###################################################################

    ###################### Side Menu Operations ######################


    def load_data_button(self):
        """
        @brief Loads the data when the 'Open Data' button is clicked.
        """
        data_path = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', "data.txt", "Data files (*.txt)")[0]
        if data_path:
            self.load_data(data_path)
            self.plot_initial_solution()
            self.change_buttons_state("source_opened", False)

    def initial_solution_button_clicked(self):
        """
        @brief Handles events when buttons related to the initial solution are clicked.
        """
        sender_name = self.sender().text().replace("menu_", "")
        
        # Save to selected path
        if sender_name == 'Save As':
            with open(QtWidgets.QFileDialog.getSaveFileName(self, 'Save As', "initial_solution.txt", "Text files (*.txt)")[0], 'w') as f:
                for point in self.get_data():
                    f.write(str(point.get_coordinates()[0]) + " " + str(point.get_coordinates()[1]) + "\n")
        
        # Save to exact path
        elif sender_name == 'Save':
            with open("initial_solution.txt", 'w') as f:
                for point in self.get_data():
                    f.write(str(point.get_coordinates()[0]) + " " + str(point.get_coordinates()[1]) + "\n")
        
        # Export as jpg
        elif sender_name == 'Export As':
            self.monitor_initial_solution.pixmap().save(QtWidgets.QFileDialog.getSaveFileName(self, 'Export As', "initial_solution.png", "Images (*.png)")[0])
        
        # Undo and Redo operations
        elif sender_name == 'Undo':
            if self.initial_solution_hist_index < len(self.initial_solution_png_hist) - 1:

                # Update the initial solution plot
                self.initial_solution_hist_index += 1
                self.monitor_initial_solution.setPixmap(self.initial_solution_png_hist[self.initial_solution_hist_index])
        
        elif sender_name == 'Redo':            
            if self.initial_solution_hist_index > 0:

                # Update the initial solution plot
                self.initial_solution_hist_index -= 1
                self.monitor_initial_solution.setPixmap(self.initial_solution_png_hist[self.initial_solution_hist_index])
            

    def final_solution_button_clicked(self):
        """
        @brief Handles events when buttons related to the final solution are clicked.
        """

        sender_name = self.sender().text().replace("menu_", "")

        # Save to selected path
        if sender_name == 'Save As': 
            with open(QtWidgets.QFileDialog.getSaveFileName(self, 'Save As', "final_solution.txt", "Text files (*.txt)")[0], 'w') as f:
                for point in self.get_data():
                    f.write(str(point.get_coordinates()[0]) + " " + str(point.get_coordinates()[1]) + " cluster: " + str(point.get_cluster_id()) + "\n")
                
        # Save to exact path
        elif sender_name == 'Save':
            with open("final_solution.txt", 'w') as f:
                for point in self.get_data():
                    f.write(str(point.get_coordinates()[0]) + " " + str(point.get_coordinates()[1]) + " cluster: " + str(point.get_cluster_id()) + "\n")
        
        # Export as jpg
        elif sender_name == 'Export As':
            self.monitor_final_solution.pixmap().save(QtWidgets.QFileDialog.getSaveFileName(self, 'Export As', "final_solution.png", "Images (*.png)")[0])

        elif sender_name == 'Undo':
            if self.final_solution_hist_index < len(self.final_solution_png_hist) - 1:
                # Plot the previous solution
                self.final_solution_hist_index += 1
                self.monitor_final_solution.setPixmap(self.final_solution_png_hist[self.final_solution_hist_index])

                # Update the results panel
                self.results_panel_hist_index += 1
                self.monitor_results.setPlainText(self.results_panel_hist[self.results_panel_hist_index])

                # Update the information panel
                self.information_panel_hist_index += 1
                self.monitor_information_panel.setPlainText(self.information_panel_hist[self.information_panel_hist_index])
            
            if self.hubs_hist_index < len(self.hubs_hist) - 1:
                self.hubs_hist_index += 1
                self.manual_hubs.setPlainText(self.hubs_hist[self.hubs_hist_index])
                
                self.nodes_hist_index += 1
                self.manual_nodes.setPlainText(self.nodes_hist[self.nodes_hist_index])

        elif sender_name == 'Redo':
            if self.final_solution_hist_index > 0:
                # Plot the previous solution
                self.final_solution_hist_index -= 1
                self.monitor_final_solution.setPixmap(self.final_solution_png_hist[self.final_solution_hist_index])

                # Update the results panel
                self.results_panel_hist_index -= 1
                self.monitor_results.setPlainText(self.results_panel_hist[self.results_panel_hist_index])

                # Update the information panel
                self.information_panel_hist_index -= 1
                self.monitor_information_panel.setPlainText(self.information_panel_hist[self.information_panel_hist_index])

            if self.hubs_hist_index > 0:
                self.hubs_hist_index -= 1
                self.manual_hubs.setPlainText(self.hubs_hist[self.hubs_hist_index])
                
                self.nodes_hist_index -= 1
                self.manual_nodes.setPlainText(self.nodes_hist[self.nodes_hist_index])
                

    ##############################################################

    ###################### Other Operations #####################

    def exit_app(self):
        """
        @brief Exits the application.
        """
        sys.exit()

    def plot_to_pixmap(self, fig, label_size):
        """
        @brief Converts a matplotlib figure to a QPixmap.
        @param fig: The matplotlib figure to be converted.
        @param label_size: The size of the label for the conversion.
        @return QPixmap: The converted QPixmap.
        """
        fig.canvas.draw()
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        img = cv2.resize(img, label_size)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return self.cv2_to_pixmap(img)

    def cv2_to_pixmap(self, img):
        """
        @brief Converts an OpenCV image to a QPixmap.
        @param img: The OpenCV image to be converted.
        @return QPixmap: The converted QPixmap.
        """
        height, width, channel = img.shape
        bytesPerLine = 3 * width
        qImg = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
        return QPixmap(qImg)
    
    # Figure initialization
    def init_figure(self):
        """
        @brief Initializes a matplotlib figure.
        @return fig: The initialized matplotlib figure.
        @return ax: The axis object associated with the figure.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        return fig, ax

