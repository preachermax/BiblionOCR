import filecmp
import os
import shutil
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

module_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(module_dir, '..', '..'))

if module_dir not in sys.path:
    sys.path.insert(0, module_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from PyQt5 import QtGui, QtWidgets

import MyPixler
import MyServer


def make_sample_copy(source_path, suffix):
    temp_dir = tempfile.mkdtemp(prefix='biblion_pixler_loop_')
    target_path = os.path.join(temp_dir, f'sample_copy{suffix}')
    shutil.copy2(source_path, target_path)
    return target_path


def main():
    sample_image = os.environ.get(
        'BIBLION_SMOKE_IMAGE',
        os.path.join(
            repo_root,
            'ViewController',
            '1-PreProcess',
            'ImageEditor',
            'Image-Editor-main',
            'ppl.jpg',
        ),
    )

    if not os.path.isfile(sample_image):
        raise FileNotFoundError(sample_image)

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    qimage = QtGui.QImage(sample_image)
    assert not qimage.isNull(), 'Failed to load sample image into QImage'

    cropped = MyPixler.PixlerMain.crop_processor(None, qimage, {'x': 10, 'y': 10, 'w': 50, 'h': 60})
    assert not cropped.isNull(), 'Crop processor returned a null image'

    return_dir = tempfile.mkdtemp(prefix='biblion_pixler_return_')
    return_path = os.path.join(return_dir, 'pixler_return.tif')
    MyPixler.PixlerMain._save_qimage_as_tiff(None, cropped, return_path)
    assert os.path.isfile(return_path), 'MyPixler did not write the return file'

    source_copy = make_sample_copy(sample_image, '.tif')
    source_original_bytes = open(source_copy, 'rb').read()

    server = MyServer.MainWindow.__new__(MyServer.MainWindow)
    server.pixler_return_path = ''
    server.pending_pixler_source_path = ''
    server.imgpath = source_copy
    server.showImage = lambda path: setattr(server, '_showImage_called_with', path)

    accepted = MyServer.MainWindow.consume_pixler_return(
        server,
        return_path,
        source_copy,
        overwrite=False,
    )

    assert accepted is True, 'MyServer did not accept the returned crop file'
    assert server.pixler_return_path == os.path.normpath(return_path)
    assert server.pending_pixler_source_path == os.path.normpath(source_copy)
    assert open(source_copy, 'rb').read() == source_original_bytes, 'Source file changed even though overwrite=False'

    source_copy_overwrite = make_sample_copy(sample_image, '_overwrite.tif')
    server2 = MyServer.MainWindow.__new__(MyServer.MainWindow)
    server2.pixler_return_path = ''
    server2.pending_pixler_source_path = ''
    server2.imgpath = source_copy_overwrite
    server2.showImage = lambda path: setattr(server2, '_showImage_called_with', path)

    accepted = MyServer.MainWindow.consume_pixler_return(
        server2,
        return_path,
        source_copy_overwrite,
        overwrite=True,
    )

    assert accepted is True, 'MyServer overwrite path did not accept the returned crop file'
    assert filecmp.cmp(return_path, source_copy_overwrite, shallow=False), 'Returned crop was not written back to the source copy'
    assert server2.imgpath == os.path.normpath(source_copy_overwrite)
    assert getattr(server2, '_showImage_called_with', None) == source_copy_overwrite

    print('TEST_OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
