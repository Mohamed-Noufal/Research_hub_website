import { useState } from 'react';
import { Resizable } from 're-resizable';
import NotesLibrary from './NotesLibrary';
import NotesEditor from './NotesEditor';

export default function NotesManager() {
    const [activeNoteId, setActiveNoteId] = useState<string | null>(null);
    const [sidebarWidth, setSidebarWidth] = useState(300);

    return (
        <div className="flex h-full w-full overflow-hidden bg-white">
            <Resizable
                size={{ width: sidebarWidth, height: '100%' }}
                onResizeStop={(_e, _direction, _ref, d) => {
                    setSidebarWidth(sidebarWidth + d.width);
                }}
                minWidth={200}
                maxWidth={600}
                enable={{ right: true }}
                className="border-r border-gray-200 bg-gray-50 flex flex-col"
            >
                <NotesLibrary onOpenNote={setActiveNoteId} />
            </Resizable>

            <div className="flex-1 h-full overflow-hidden bg-white">
                {activeNoteId ? (
                    <NotesEditor noteId={activeNoteId} />
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                        <p>Select a note to start writing</p>
                    </div>
                )}
            </div>
        </div>
    );
}

