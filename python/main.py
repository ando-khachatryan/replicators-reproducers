import sim
import click

@click.command()
@click.option('--folder', required=True, 
              type=str, help='The folder root folder of the simulation, must contain sim.yaml file')
def run(folder: str):
    sim.run_from_folder(folder)

if __name__ == '__main__':
    run()