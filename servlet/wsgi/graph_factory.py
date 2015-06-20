import pygal

__author__ = 'shawkins'

class SmartGraph:

    NUMBER_DATA_KEY = "number_data"
    COLOR_KEY = "color"

    def __init__(self, Classtype, group_titles=None, graph_data=None, title=None, width=800, palette=None):
        """
        :param Classtype: <class>: the pygal class type to instantiate (e.g. pygal.Line, pygal.Bar, etc)
        :param group_titles: [str]:  Array of bar-group titles (e.g. ["2015.2", "2015.3"]
        :param graph_data: dict: example format shown below
        :param title: str:  Title of graph. When used with Dashboard, should be left as None
        :param dashing_num_columns: int between 1 and 2: the number of columns wide that the graph should render to
        :param dashing_num_rows: int between 1 and 2: the number of rows tall that the graph should render to

        example data format:

        graph_data = {
            'Passed': {
                'number_data': [13,12],
                'color':'#440000'         # Color key is optional
            }
            'Failed': {
                'number_data': [22,18],
                'color': '#004400'        # Color key is optional
            }
            'Inconclusive': {
                'number_data': [15, 18],
                'color':'#000044'         # color key is optional
            }
        }

        Note that the 'color' key is optional, but if used, ALL data series must have an associated color, or colors
        may not match!

        group_titles = ["2015.1", "2015.2"]
        """
        if group_titles is None:
            group_titles = []
        if graph_data is None:
            graph_data = {}
        # title can be left as None

        if palette is None:
            palette = {
                "red":"#D92525",
                "yellow": "#F29F05",
                "green": "#88A61B",
                "blue":"#0E3D59",
                "orange":"#F25C05",
                "dark_gray": "#808080"
            }

        self.palette = palette

        default_style = pygal.style.Style(foreground_dark="#DDD", foreground_light="#DDD", background="#222",
                                          plot_background="transparent",
                                          colors=(self.palette['red'], self.palette['yellow'], self.palette['green'],
                                                  self.palette['orange'], self.palette['blue']))

        # LOCAL PROPERTIES
        self.color_list = []
        self.Classtype = Classtype
        self.graph_data = graph_data

        # PYGAL PROPERTIES
        # all of these options are documented by pygal: http://pygal.org/ and http://pygal.org/styles/
        self.fill = True
        self.group_titles = group_titles
        self.include_x_axis = False
        self.label_font_size = 18
        self.legend_at_bottom = True
        self.legend_font_size = 18
        self.major_label_font_size = 20
        self.margin_bottom = 0
        self.margin_left = 0
        self.margin_right = 0
        self.margin_top = 0
        self.order_min = -15
        self.rounded_bars = 0
        self.show_dots = True
        self.show_legend = True
        self.show_minor_x_labels = True
        self.show_minor_y_labels = True
        self.show_x_guides = True
        self.show_x_labels = True
        self.show_y_guides = True
        self.show_y_labels = True
        self.spacing = 15
        self.stacked = True
        self.stroke = True
        self.style = default_style
        self.title = title
        self.title_font_size = 24
        self.truncate_label = 20
        self.value_font_size = 18
        self.width = width
        self.x_label_rotation = 0
        self.x_title = None
        self.y_label_rotation = 0
        self.y_labels_major_count = 4
        self.y_title = None

        # If the graph is short, don't render minor y labels, they get too cluttered
        # if height < 500:
        #     self.show_minor_y_labels = False

    @classmethod
    def LineGraph(cls, **args):
        """
        :param args: all arguments a standard SmartGraph would expect
        :return: SmartGraph instance based on a pygal.Line
        """
        return SmartGraph(pygal.Line, **args)

    @classmethod
    def StackedLineGraph(cls, **args):
        """
        :param args: all arguments a standard SmartGraph would expect
        :return: SmartGraph instance based on a pygal.StackedLine
        """
        return SmartGraph(pygal.StackedLine, **args)

    @classmethod
    def BarGraph(cls, **args):
        """
        :param args: all arguments a standard SmartGraph would expect
        :return: SmartGraph instance based on a pygal.Bar
        """
        return SmartGraph(pygal.Bar, **args)

    @classmethod
    def StackedBarGraph(cls, **args):
        """
        :param args: all arguments a standard SmartGraph would expect
        :return: SmartGraph instance based on a pygal.StackedBar
        """
        return SmartGraph(pygal.StackedBar, **args)

    def set_dimensions(self, new_dimensions):
        self.width = new_dimensions[0]
        self.height = new_dimensions[1]

    def create_graph_object(self):
        """
        Creates a pygal.Graph object with all of our properties

        :return: pygal.Graph instance
        """
        graph = self.Classtype()

        # Check each of our own properties, and if they match a pygal config property, put them in
        for key in self.__dict__.keys():
            if self.__dict__[key] is not None:
                pygal_configs = [p.name for p in pygal.config.CONFIG_ITEMS]
                if key in pygal_configs:
                    setattr(graph, key, self.__dict__[key])

        graph.x_labels = self.group_titles

        # Append each series to the pygal graph
        for series_key in self.graph_data.keys():
            series_title = series_key
            if SmartGraph.COLOR_KEY in self.graph_data[series_key]:
                series_color = self.graph_data[series_key][SmartGraph.COLOR_KEY]
                self.color_list.append(series_color)
            graph.add(series_title, self.graph_data[series_key][SmartGraph.NUMBER_DATA_KEY])

        # Update custom colors in graph before render, if we have any
        if len(self.color_list) > 0:
            self.style.colors = self.color_list
            graph.style = self.style

        return graph

    def insert_series(self, series_name, series_data, series_color=None):
        self.graph_data[series_name] = {}
        self.graph_data[series_name][SmartGraph.NUMBER_DATA_KEY] = series_data
        if series_color is not None:
            self.graph_data[series_name][SmartGraph.COLOR_KEY] = series_color