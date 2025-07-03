import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

from datetime import datetime, timedelta
from matplotlib import font_manager
from loguru import logger

from . import pathes


font_properties = font_manager.FontEntry(fname=pathes.font_path, name="minecraft")
font_manager.fontManager.ttflist.append(font_properties)


def create_plot(data_dict, output_file=pathes.chart_path, time_range_days=None):
    "Фукнция для создания линейного графика"

    "Данные"
    dates = [datetime.strptime(date, "%Y.%m.%d") for date in data_dict.keys()]
    values = list(data_dict.values())

    "Шрифт"
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = font_properties.name
    prop = font_manager.FontProperties(fname=pathes.font_path)
    title_font = {
        "fontproperties": prop,
        "fontsize": 16,
        "fontweight": "bold",
        "color": "white",
    }
    label_font = {"fontproperties": prop, "fontsize": 11, "color": "white"}
    tick_font = {"fontproperties": prop, "fontsize": 10, "color": "lightgray"}
    logger.info("Загружен шрифт {}".format(font_properties.name))

    "Фильтрация данных"
    if time_range_days is not None:
        today = max(dates) if dates else datetime.now()
        cutoff_date = today - timedelta(days=time_range_days)
        filtered_data = [
            (date, value) for date, value in zip(dates, values) if date >= cutoff_date
        ]
        if filtered_data:
            dates, values = zip(*filtered_data)
        else:
            dates, values = [], []

    "Наведение красоты"
    plt.style.use("dark_background")
    sns.set_style(
        "darkgrid",
        {
            "axes.facecolor": "#1e1e1e",  # фон области графика
            "figure.facecolor": "#1e1e1e",  # фон вокруг графика
            "grid.color": "#3d3d3d",  # цвет сетки
            "text.color": "white",  # цвет текста
        },
    )
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#1e1e1e")  # основной фон

    "Линия графика"
    sns.lineplot(
        x=dates,
        y=values,
        marker="o",
        color="#ff8222",
        linewidth=3,
        markersize=0,
        markerfacecolor="white",
        ax=ax,
    )

    "Названия колонок"
    ax.set_title("Статистика", **title_font)
    ax.set_xlabel("Дата", **tick_font)
    ax.set_ylabel("Сообщений", **label_font)

    "Оси"
    ax.tick_params(colors="lightgray")
    for spine in ax.spines.values():
        spine.set_color("#3d3d3d")
    for label in ax.get_xticklabels():
        label.set_fontproperties(prop)
        label.set_color("lightgray")
    for label in ax.get_yticklabels():
        label.set_fontproperties(prop)
        label.set_color("lightgray")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m.%d"))
    plt.xticks(rotation=90)

    "Cетка"
    ax.grid(True, linestyle="--", alpha=0.5, color="#3d3d3d")

    "Подписи"
    n = 0

    for date, value in zip(dates, values):
        if n % 2 == 0:
            ax.text(
                date,
                value + 5,
                str(value),
                ha="center",
                va="bottom",
                fontsize=9,
                color="white",
                bbox=dict(
                    facecolor="#333333",
                    alpha=0.7,
                    edgecolor="none",
                    boxstyle="round,pad=0.2",
                ),
            )
        n += 1
    ax.set_facecolor("#1e1e1e")
    plt.tight_layout()

    "Сохранение графика"
    plt.savefig(
        output_file,
        dpi=300,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
        bbox_inches="tight",
    )
    plt.close()
    logger.info("График сохранён")
