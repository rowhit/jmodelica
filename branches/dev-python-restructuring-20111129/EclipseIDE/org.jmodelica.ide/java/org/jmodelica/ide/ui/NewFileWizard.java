/*
    Copyright (C) 2009 Modelon AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
package org.jmodelica.ide.ui;


import org.eclipse.core.resources.IFile;
import org.eclipse.core.resources.IResource;
import org.eclipse.core.runtime.IConfigurationElement;
import org.eclipse.jface.viewers.IStructuredSelection;
import org.eclipse.jface.wizard.Wizard;
import org.eclipse.ui.INewWizard;
import org.eclipse.ui.IWorkbench;
import org.eclipse.ui.IWorkbenchPage;
import org.eclipse.ui.IWorkbenchWindow;
import org.eclipse.ui.PartInitException;
import org.eclipse.ui.dialogs.WizardNewFileCreationPage;
import org.eclipse.ui.ide.IDE;
import org.eclipse.ui.part.ISetSelectionTarget;
import org.jmodelica.ide.IDEConstants;
import org.jmodelica.ide.helpers.Util;

public class NewFileWizard extends Wizard implements INewWizard {

	private static final String WINDOW_TITLE = "New Modelica File";
	private static final String TITLE = "New Modelica File";
	private static final String DESCRIPTION = "Creates a new Modelica File";
	private static final String FILE_EXTENSION = IDEConstants.MODELICA_FILE_EXT;

	private IWorkbench workbench;
	private IStructuredSelection selection;
	private WizardNewFileCreationPage mainPage;

	@Override
	public boolean performFinish() {
		
		IFile file = mainPage.createNewFile();
		if (file == null) {
			return false;
		}

		selectAndReveal(file);

		// Open editor on new file.
		IWorkbenchWindow dw = getWorkbench().getActiveWorkbenchWindow();
		try {
			if (dw != null) {
				IWorkbenchPage page = dw.getActivePage();
				if (page != null) {
					IDE.openEditor(page, file, true);
				}
			}
		} catch (PartInitException e) {
			// TODO add some error handling code here
		}

		return true;
	}

	public void init(IWorkbench workbench, IStructuredSelection selection) {
		this.workbench = workbench;
		this.selection = selection;
		setWindowTitle(WINDOW_TITLE);
	}

	protected IStructuredSelection getSelection() {
		return selection;
	}

	protected IWorkbench getWorkbench() {
		return workbench;
	}

	@Override
	public void addPages() {
		super.addPages();
		mainPage = new WizardNewFileCreationPage(WINDOW_TITLE, getSelection());//$NON-NLS-1$
		mainPage.setTitle(TITLE);
		mainPage.setDescription(DESCRIPTION);
		mainPage.setFileExtension(FILE_EXTENSION);
		addPage(mainPage);
	}

	/*
	 * The rest of the code in this file is from BasicNewResourceWizard in
	 * org.eclipse.ui.wizards.newresource which reveals a newly created resource
	 * as much as possible
	 */

	/**
	 * Selects and reveals the newly added resource in all parts of the active
	 * workbench window's active page.
	 * 
	 * @see ISetSelectionTarget
	 */
	protected void selectAndReveal(IResource newResource) {
		Util.selectAndReveal(newResource, getWorkbench().getActiveWorkbenchWindow());
	}

}
